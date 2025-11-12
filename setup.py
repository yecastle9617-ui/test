from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="myproject",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="프로젝트에 대한 간단한 설명",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/myproject",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # requirements.txt의 내용을 여기에 추가하거나
        # requirements.txt를 읽어올 수 있습니다
    ],
)

