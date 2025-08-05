from setuptools import setup

setup(
    name="docker-honeypot",
    version="0.1.0",
    author="Niraj Bagde",
    description="A Python Docker-based honeypot(prototype) with isolated filesystem which is useful for the understanding the attacks",
    url="https://github.com/NirajBagde1978/docker-honeypot",
    py_modules=["main"],
    install_requires=[
        "docker>=5.0.0",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'docker-honeypot = main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
    ],
)
