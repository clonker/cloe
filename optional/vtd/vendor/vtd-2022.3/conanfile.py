# mypy: ignore-errors
# pylint: skip-file

import os
import os.path
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from conans import CMake, ConanFile, tools
from conans.errors import ConanInvalidConfiguration


def patch_rpath(file: Path, rpath: List[str]):
    """Set the RPATH of an executable or library.

    This will fail silently if the file is not an ELF executable.
    """
    assert file.exists()

    # Get original RPATH of file, or fail.
    result = subprocess.run(
        ["patchelf", "--print-rpath", str(file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.stderr.decode().strip() == "not an ELF executable":
        # Silently ignore binaries that don't apply.
        return
    original = result.stdout.decode().strip()
    if original != "":
        rpath.append(original)

    file_arg = str(file)
    rpath_arg = ":".join(rpath)
    print(f"Setting RPATH: {file_arg} -> {rpath_arg}")
    subprocess.run(
        ["patchelf", "--set-rpath", rpath_arg, file_arg],
        check=True,
    )


def find_binary_files() -> List[Path]:
    """Return a list of all file paths that are of the binary type."""
    result = subprocess.run(
        """find -type f -executable -exec sh -c "file -i '{}' | grep -q '; charset=binary'" \; -print""",
        shell=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    return [Path(x) for x in result.stdout.decode().splitlines()]


def remove_broken_symlinks() -> None:
    """Remove all broken symlinks that are in the vtd_folder."""
    subprocess.run(
        """rm $(find . -xtype l)""",
        shell=True,
        stdout=subprocess.PIPE,
        check=True,
    )


class VtdConan(ConanFile):
    name = "vtd"
    version = "2022.3"
    license = "Proprietary"
    url = "https://vires.mscsoftware.com"
    no_copy_source = True
    description = "Include binary files in C/C++"
    topics = ("simulator", "vires")
    settings = "os", "arch"
    options = {
        "with_osi": [True, False],
        "with_road_designer": [True, False],
        "with_image_generator": [True, False],
    }
    default_options = {
        "with_osi": True,
        "with_road_designer": False,
        "with_image_generator": False,
    }

    _archive_base = "dl/VTD.2022.3.tgz"
    _archive_osi = "dl/vtd.2020.addOns.OSI.20200826.tgz"
    _archive_rod = "dl/vtd.2021.1.addOns.World.Edit.Base.20210511.tgz"
    _root_dir = "VTD.2022.3"

    def export_sources(self):
        self.copy("libdeps_pruned.txt")
        self.copy(self._archive_base, symlinks=False)
        if Path(self._archive_osi).exists():
            self.copy(self._archive_osi, symlinks=False)
        if Path(self._archive_rod).exists():
            self.copy(self._archive_rod, symlinks=False)

    def configure(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("VTD binaries do not exist for Windows")

    def build(self):
        src = Path(self.source_folder)
        dst = Path(self.build_folder)
        vtddir = dst / "VTD.2022.3"
        libdir = vtddir / "bundled"

        def extract_archive(archive):
            print(f"Extracting: {archive}")
            tools.untargz(src / archive, dst)

        extract_archive(self._archive_base)
        libdir.mkdir()
        if self.options.with_osi:
            extract_archive(self._archive_osi)
        if self.options.with_road_designer:
            extract_archive(self._archive_rod)
        if not self.options.with_image_generator:
            path = Path(vtddir / "Runtime/Core/IG64").resolve()
            shutil.rmtree(path)
            Path(vtddir / "Runtime/Core/ImageGenerator").unlink()
            remove_broken_symlinks()

        # Patch RPATH of several critical binaries.
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager/moduleManager.2022.3.40_flexlm",
            ["$ORIGIN/../Lib", "$ORIGIN/lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager/lib/libVTDModulePlugin.so.2022",
            ["$ORIGIN/../../Lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager/lib/libprotobuf.so.9",
            ["$ORIGIN/../../Lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager/lib/libopen_simulation_interface.so",
            ["$ORIGIN/../../Lib", "$ORIGIN"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager.cxx98/moduleManager.2022.3.40_flexlm",
            ["$ORIGIN/../Lib", "$ORIGIN/lib"],
        )
        patch_rpath(
            vtddir
            / "Runtime/Core/ModuleManager.cxx98/lib/libopen_simulation_interface.so",
            ["$ORIGIN/../../Lib", "$ORIGIN"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager.cxx98/lib/libprotobuf.so.9",
            ["$ORIGIN/../../Lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager.cxx98/lib/libVTDModulePlugin.so",
            ["$ORIGIN/../../Lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager.cxx11/moduleManager.2022.3.40_flexlm",
            ["$ORIGIN/../Lib", "$ORIGIN/lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager.cxx11/lib/libVTDModulePlugin.so.2022",
            ["$ORIGIN/../../Lib"],
        )
        patch_rpath(
            vtddir
            / "Runtime/Core/ModuleManager.cxx11/lib/libopen_simulation_interface.so",
            ["$ORIGIN/../../Lib", "$ORIGIN"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ModuleManager.cxx11/lib/libprotobuf.so.9",
            ["$ORIGIN/../../Lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/ParamServer/paramServer.2022.3.40",
            ["$ORIGIN/../Lib"],
        )
        patch_rpath(
            vtddir / "Runtime/Core/Traffic/ghostdriver.2022.3.40_flexlm",
            ["$ORIGIN/../Lib"],
        )

        # Patch RPATH of all the binaries with the path to our bundled system libraries:
        for file in find_binary_files():
            try:
                patch_rpath(
                    file,
                    [
                        f"$ORIGIN/{os.path.relpath(libdir, (dst / file).parent)}",
                        "$ORIGIN",
                    ],
                )
            except:
                # Not all files can be set, but even if this happens it doesn't appear
                # to be a big deal.
                print(f"Error: cannot set RPATH of {file}", file=sys.stderr)

        # Bundle libraries that we need at runtime so that this package is portable:
        with Path(src / "libdeps_pruned.txt").open() as file:
            libraries = [Path(x.strip()) for x in file.read().splitlines()]
        for path in libraries:
            print(f"Bundling system library: {path}")
            if path.is_symlink():
                shutil.copy(path, libdir, follow_symlinks=False)
                path = path.resolve(strict=True)
            assert not path.is_symlink()
            shutil.copy(path, libdir)
            patch_rpath(libdir / path.name, ["$ORIGIN"])

    def package(self):
        self.copy("*", src=self._root_dir, symlinks=True)

    def package_info(self):
        bindir = Path(self.package_folder) / "bin"
        self.output.info(f"Appending PATH environment variable: {bindir}")
        self.env_info.PATH.append(str(bindir))
        self.env_info.VTD_ROOT = self.package_folder
        if self.options.with_osi:
            osi_path = (
                Path(self.package_folder)
                / "Data/Setups/Standard.OSI3/Bin/libopen_simulation_interface.so"
            )
            if not osi_path.exists():
                raise ConanInvalidConfiguration("VTD OSI library not found.")
            self.env_info.VTD_EXTERNAL_MODELS.append(f"{osi_path}")
