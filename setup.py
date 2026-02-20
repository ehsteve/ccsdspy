import os

from setuptools import Extension, setup


def _build_extensions():
    build_cython = os.environ.get("CCSDSPY_BUILD_CYTHON", "0")
    if build_cython.lower() not in {"1", "true", "yes", "on"}:
        return []

    from Cython.Build import cythonize

    extensions = [
        Extension(
            "ccsdspy._varlength_cython",
            ["ccsdspy/_varlength_cython.pyx"],
        )
    ]
    return cythonize(extensions, compiler_directives={"language_level": "3"})


setup(ext_modules=_build_extensions())
