from setuptools import setup, find_packages

setup(
    name="jingshuonium",
    version="0.1.0",
    description="A 2D Minecraft-like game built with Pygame",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[
        "pygame>=2.0.0",
        "perlin-noise>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "jingshuonium=game.main:main",
        ],
    },
    package_data={
        "": ["assets/textures/*", "assets/sounds/*", "assets/fonts/*"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)