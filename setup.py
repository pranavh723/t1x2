from setuptools import setup, find_packages

setup(
    name="t1x2y1",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot",
        # Add other dependencies from requirements.txt
    ],
    entry_points={
        'console_scripts': [
            't1x2y1=t1x2y1.run:run_bot',
        ],
    },
)