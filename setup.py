import os
import sys
import subprocess
import setuptools
from setuptools import setup
from setuptools.command.build_ext import build_ext
import shutil
import glob
import sysconfig
import platform

if 'VERSION' not in os.environ:
    os.environ['VERSION'] = '0.0.0'
version = os.environ['VERSION']

class CMakeBuild(build_ext):
    def run(self):
        cmake_dir = os.path.abspath(os.path.dirname(__file__))
        build_temp = os.path.abspath(self.build_temp)
        os.makedirs(build_temp, exist_ok=True)

        # get SVF_DIR, LLVM_DIR, Z3_DIR from env, otherwise abort
        if "SVF_DIR" not in os.environ:
            raise RuntimeError("SVF_DIR not set")
        SVF_DIR = os.environ["SVF_DIR"]
        if not os.path.exists(os.path.join(SVF_DIR, "Release-build")):
            raise RuntimeError("SVF_DIR/Release-build not found")

        # get LLVM_DIR from env, otherwise abort
        if "LLVM_DIR" not in os.environ:
            raise RuntimeError("LLVM_DIR not set")
        LLVM_DIR = os.environ["LLVM_DIR"]
        if not os.path.exists(LLVM_DIR):
            raise RuntimeError("LLVM_DIR not found")

        # get Z3_DIR from env, otherwise abort
        if "Z3_DIR" not in os.environ:
            raise RuntimeError("Z3_DIR not set")
        Z3_DIR = os.environ["Z3_DIR"]
        if not os.path.exists(os.environ["Z3_DIR"]):
            raise RuntimeError("Z3_DIR not found")

        # get PYBIND11_DIR from env, otherwise abort
        if "PYBIND11_DIR" not in os.environ:
            raise RuntimeError("PYBIND11_DIR not set")

        if "CMAKE_BUILD_TYPE" not in os.environ:
            CMAKE_BUILD_TYPE = "Release"
        else:
            CMAKE_BUILD_TYPE = os.environ["CMAKE_BUILD_TYPE"]

        # Run CMake
        subprocess.run(
            [
                "cmake", cmake_dir,
                "-G", "Unix Makefiles",
                "-DCMAKE_BUILD_TYPE=Release",
                "-DLLVM_DIR="+LLVM_DIR,
                "-DSVF_DIR="+SVF_DIR,
                "-DZ3_DIR="+Z3_DIR,
                "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON"
                "-DCMAKE_PREFIX_PATH="+os.environ["PYBIND11_DIR"],
                "-Dpybind11_DIR="+os.environ["PYBIND11_DIR"],
                "-DCMAKE_BUILD_TYPE=" + CMAKE_BUILD_TYPE,
                "-DPython3_EXECUTABLE=" + sys.executable,
                ],
            cwd=build_temp,
            check=True
        )



        # Build the project
        subprocess.run(["cmake", "--build", "."], cwd=build_temp, check=True)

        # Find the generated shared library (libpysvf.so)
        built_so = glob.glob(os.path.join(build_temp, "**", "libpysvf.so"), recursive=True)
        if not built_so:
            raise RuntimeError("Could not find built libpysvf.so")

        # Rename and move to expected location
        # get dylib suffix of current python version（e.g cpython-38-x86_64-linux-gnu.so）
        so_suffix = sysconfig.get_config_var("EXT_SUFFIX")

        so_target = os.path.join(self.build_lib, "pysvf", "pysvf" + so_suffix)
        os.makedirs(os.path.dirname(so_target), exist_ok=True)
        shutil.copyfile(built_so[0], so_target)
        # if platform is darwin, we need to change the libz3.dylib path in pysvf.{$SO_SUFFIX}
        # run  install_name_tool -change libz3.dylib @rpath/libz3.dylib pysvf.{$SO_SUFFIX}  to so_target
        if platform.system() == "Darwin":
            subprocess.run(["install_name_tool", "-change", "libz3.dylib", "@rpath/libz3.dylib", so_target], check=True)

        # if pysvf/SVF/Release-build exist, remove
        if os.path.exists(os.path.join(self.build_lib, "pysvf", "SVF")):
            shutil.rmtree(os.path.join(self.build_lib, "pysvf", "SVF"))
            print("Remove old "+os.path.join(self.build_lib, "pysvf", "SVF"))

        # mkdir -p pysvf/SVF/Release-build
        os.makedirs(os.path.join(self.build_lib, "pysvf", "SVF/Release-build"), exist_ok=True)
        # cp -rf $GITHUB_WORKSPACE/Release-build/include SVF-${osVersion}/Release-build/
        # cp -rf $GITHUB_WORKSPACE/svf/include SVF-${osVersion}/Release-build/
        # cp -rf $GITHUB_WORKSPACE/svf-llvm/include SVF-${osVersion}/Release-build/
        # cp -rf $GITHUB_WORKSPACE/Release-build/lib SVF-${osVersion}/Release-build/
        # cp -rf $GITHUB_WORKSPACE/Release-build/bin SVF-${osVersion}/Release-build/
        shutil.copytree(os.path.join(SVF_DIR, CMAKE_BUILD_TYPE+"-build", "include"), os.path.join(self.build_lib, "pysvf", "SVF", "Release-build", "include"),dirs_exist_ok=True)
        if os.path.exists(os.path.join(SVF_DIR, "svf", "include")):
            shutil.copytree(os.path.join(SVF_DIR, "svf", "include"), os.path.join(self.build_lib, "pysvf", "SVF", "Release-build", "include"),dirs_exist_ok=True)
        if os.path.exists(os.path.join(SVF_DIR, "svf-llvm", "include")):
            shutil.copytree(os.path.join(SVF_DIR, "svf-llvm", "include"), os.path.join(self.build_lib, "pysvf", "SVF", "Release-build", "include"),dirs_exist_ok=True)
        shutil.copytree(os.path.join(SVF_DIR, CMAKE_BUILD_TYPE+"-build", "lib"), os.path.join(self.build_lib, "pysvf", "SVF", "Release-build", "lib"),dirs_exist_ok=True)
        shutil.copytree(os.path.join(SVF_DIR, CMAKE_BUILD_TYPE+"-build", "bin"), os.path.join(self.build_lib, "pysvf", "SVF", "Release-build", "bin"),dirs_exist_ok=True)

        # cp -rf $GITHUB_WORKSPACE/z3/bin .build_lib/pysvf/z3/bin
        # if exist bin or lib
        if os.path.exists(os.path.join(os.environ["Z3_DIR"], "bin")):
            shutil.copytree(os.path.join(os.environ["Z3_DIR"], "bin"), os.path.join(self.build_lib, "pysvf", "SVF", "z3.obj", "bin"),dirs_exist_ok=True)
        if os.path.exists(os.path.join(os.environ["Z3_DIR"], "lib")):
            shutil.copytree(os.path.join(os.environ["Z3_DIR"], "lib"), os.path.join(self.build_lib, "pysvf", "SVF", "z3.obj", "lib"),dirs_exist_ok=True)


setup(
    name="pysvf",
    version=version,
    author="Your Name",
    description="SVF with Python bindings",
    packages=setuptools.find_packages(),
    ext_modules=[setuptools.Extension("pysvf.pysvf", sources=[])],  # Placeholder for CMake
    cmdclass={"build_ext": CMakeBuild},
    package_data={
        "pysvf": ["SVF/Release-build/**/*", "z3.obj/**/*"],  # 确保 Release-build 目录被打包
    },
    include_package_data=True,
    zip_safe=False,
)

