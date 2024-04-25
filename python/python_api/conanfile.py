# mypy: ignore-errors
# pylint: skip-file

from pathlib import Path

from conan import ConanFile
from conan.tools import cmake, files, scm
from conan.tools.files import copy

required_conan_version = ">=1.52.0"


class CloeModels(ConanFile):
    name = "cloe-python-api"
    url = "https://github.com/eclipse/cloe"
    description = ""
    license = "Apache-2.0"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "pedantic": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "pedantic": True,
    }
    generators = "CMakeDeps", "VirtualRunEnv"
    no_copy_source = True
    exports_sources = [
        "cloe/*",
        "CMakeLists.txt",
    ]

    def set_version(self):
        version_file = Path(self.recipe_folder) / '..' / '..' / "VERSION"
        if version_file.exists():
            self.version = files.load(self, version_file).strip()
        else:
            git = scm.Git(self, self.recipe_folder)
            self.version = git.run("describe --dirty=-dirty")[1:]

    def requirements(self):
        self.requires(f"cloe-databroker-bindings/{self.version}@cloe/develop")
        self.requires(f"cloe-stacklib/{self.version}@cloe/develop")
        self.requires(f"cloe-simulation/{self.version}@cloe/develop")
        self.requires("pybind11/2.11.1")

    def layout(self):
        cmake.cmake_layout(self)

    def generate(self):
        tc = cmake.CMakeToolchain(self)
        tc.cache_variables["CMAKE_EXPORT_COMPILE_COMMANDS"] = True
        tc.cache_variables["CLOE_PROJECT_VERSION"] = self.version
        tc.cache_variables["TargetLintingExtended"] = self.options.pedantic
        tc.generate()

    def build(self):
        cm = cmake.CMake(self)
        if self.should_configure:
            cm.configure()
        if self.should_build:
            cm.build()

    def package(self):
        if self.should_install:
            copy(self, pattern="*.py", src=Path(self.source_folder) / 'cloe',
                 dst=Path(self.package_folder) / 'lib' / 'cloe' / 'python' / 'cloe', keep_path=True)
            cmake.CMake(self).install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "cloe-python-api")
        self.cpp_info.set_property("cmake_target_name", "cloe::python-api")
        self.cpp_info.set_property("pkg_config_name", "cloe-python-api")

        self.cpp_info.libs = files.collect_libs(self)

        if self.in_local_cache:
            self.runenv_info.prepend_path("PYTHONPATH",
                                          str(Path(self.package_folder) / 'lib' / 'cloe' / 'python'))
        else:
            self.runenv_info.prepend_path("PYTHONPATH", str(Path(self.source_folder)))