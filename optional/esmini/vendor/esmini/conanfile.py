import glob
import os
from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake
from conan.tools.files import collect_libs, patch, mkdir, copy
from conan.tools.scm import Git


class ESMini(ConanFile):
    name = "esmini"
    version = "2.24.0"
    license = "Mozilla Public License Version 2.0"
    url = "https://github.com/esmini/esmini"
    description = "Basic OpenScenario player."
    topics = ("Environment Simulator", "OpenScenario", "OpenDrive")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "test": [True, False],
        "with_osg": [True, False],
        "with_osi": [True, False],
        "with_sumo": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "test": True,
        "with_osg": False,  # todo!
        "with_osi": True,
        "with_sumo": False,
        "open-simulation-interface:shared": False,
        "cloe-osi:shared": False,
    }
    generators = "CMakeToolchain", "CMakeDeps"
    build_policy = "missing"
    no_copy_source = False

    _patch_file = Path("patches") / "esmini_2_25_1.patch"

    _pkg_scenario_dir = "scenarios"

    exports_sources = [
        "CMakeLists.txt",
        str(_patch_file),
        f"{_pkg_scenario_dir}/*",
    ]
    _git_url = "https://github.com/esmini/esmini.git"
    _git_ref = "develop" if version == "latest" else f"v{version}"
    _sim_dir = "EnvironmentSimulator"
    _test_deps = [_sim_dir, "resources", "scripts"]
    _test_dir = f"{_sim_dir}/Unittest/"
    _lib_dir = f"{_sim_dir}/Libraries/"
    _bin_dir = f"{_sim_dir}/Applications/"
    _resources_dir = f"resources"

    _protobuf_dyn = False

    def configure(self):
        if self.options.with_osg:
            self.options.with_osi = True
        if self.options.with_osi:
            self.options["open-simulation-interface"].shared = self.options.shared
            self.options["protobuf"].shared = self._protobuf_dyn
            self.options["protobuf"].debug_suffix = False

    def source(self):
        git = Git(self)
        git.fetch_commit(self._git_url, self._git_ref)

    def system_requirements(self):
        pkg_names = None
        if self.options.with_osg:
            pkg_names = [
                "libfontconfig1-dev",
                "libgl-dev",
                "libxrandr-dev",
                "libxinerama-dev",
            ]  # TODO: add all system requirements
        if pkg_names:
            from conan.tools.system.package_manager import Apt
            apt = Apt(self)
            apt.install(pkg_names, update=True, check=True)

    def requirements(self):
        if self.options.with_osi:
            self.requires("protobuf/3.15.8", override=True)
            self.requires("open-simulation-interface/3.3.1@cloe/stable")

    def generate(self):
        ext_osi = self.build_path / 'ext_osi'
        mkdir(self, ext_osi)
        copy(self, "*", src=self.dependencies["open-simulation-interface"].cpp_info.includedirs[0],
                  dst=ext_osi / 'include')
        copy(self, "*", src=self.dependencies["open-simulation-interface"].cpp_info.libdirs[0],
                  dst=ext_osi / 'lib')
        copy(self, "*", src=self.dependencies["protobuf"].cpp_info.includedirs[0],
                  dst=ext_osi / 'include')
        copy(self, "*", src=self.dependencies["protobuf"].cpp_info.libdirs[0],
                  dst=ext_osi / 'lib')

        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_PROJECT_VERSION"] = self.version
        tc.cache_variables["CMAKE_EXPORT_COMPILE_COMMANDS"] = True
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["USE_OSG"] = self.options.with_osg
        tc.cache_variables["USE_OSI"] = self.options.with_osi
        tc.cache_variables["USE_SUMO"] = self.options.with_sumo
        tc.cache_variables["USE_GTEST"] = self.options.test
        tc.cache_variables["DYN_PROTOBUF"] = True
        tc.cache_variables["CONAN_OPEN-SIMULATION-INTERFACE_ROOT"] = str(ext_osi)
        tc.generate()

    def build(self):
        trg_path = Path('.')
        patch_file = self._patch_file
        if not self.in_local_cache:
           trg_path = Path(self.source_folder) / trg_path
           patch_file = Path(self.recipe_folder) / patch_file
        patch(self, base_path=trg_path, patch_file=patch_file)

        cmake = CMake(self)
        if self.should_configure:
            cmake.configure()
        if self.should_build:
            cmake.build()
        if self.should_test:
            test_dir = Path("EnvironmentSimulator") / "Unittest"
            mkdir(self, test_dir / 'exec')
            for test in glob.glob("*_test", root_dir=Path("EnvironmentSimulator") / "Unittest"):
                gtest_filter = ""
                if test == 'ScenarioEngineDll_test':
                    gtest_filter = "--gtest_filter=-APITest.TestFetchImage"
                self.run(f"{Path('..') / test} {gtest_filter}",
                         run_environment=True, cwd=test_dir / 'exec')

    def package(self):
        cmake = CMake(self)
        cmake.install()
        self.copy(
            pattern="*.hpp",
            dst="include",
            src=Path(self.source_folder) / self._lib_dir,
            keep_path=False,
        )
        if self.options.shared:
            self.copy(pattern="*.so", dst="lib", src=self._lib_dir, keep_path=False)
        else:
            self.copy(pattern="*.a", dst="lib", src=self._lib_dir, keep_path=False)
            self.copy(pattern="*.a", dst="lib", src="bin", keep_path=False)
        apps = os.listdir(self._bin_dir)
        for app in apps:
            copy(
                self, pattern=app, dst="bin", src=f"{self._bin_dir}/{app}", keep_path=False
            )
        self.copy(
            pattern="*",
            dst=self._pkg_scenario_dir,
            src=f"{self.source_folder}/{self._resources_dir}",
        )
        xosc_dir = Path(f"{self.source_folder}/{self._pkg_scenario_dir}/xosc")
        assert xosc_dir.exists(), f"xosc dir {xosc_dir} did not exist"
        self.copy(
            "*",
            dst=self._pkg_scenario_dir,
            src=f"{self.source_folder}/{self._pkg_scenario_dir}",
        )

    def package_id(self):
        if self.options.with_osi:
            self.info.requires["open-simulation-interface"].full_package_mode()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", self.name)
        self.cpp_info.set_property("pkg_config_name", self.name)

        if self.options.shared:
            self.cpp_info.libs = collect_libs(self)
        else:
            self.cpp_info.libs = ["esminiLibStatic", "esminiRMLibStatic",
                                  "CommonMini", "RoadManager", "ScenarioEngine",
                                  "Controllers", "PlayerBase"]
            if self.options.with_osg:
                self.cpp_info.libs += ["ViewerBase"]
        self.runenv_info.define("ESMINI_XOSC_PATH", f"{self.package_folder}/{self._pkg_scenario_dir}/xosc")
