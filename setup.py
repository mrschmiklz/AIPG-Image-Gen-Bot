from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-image-generation-discord-bot",
    version="0.1.0",
    author="Your Name",
    author_email="mrschmiklz@gmail.com",
    description="A Discord bot for AI-powered image generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://https://github.com/mrschmiklz/AIPG-Image-Gen-Bot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "nextcord==2.3.2",
        "python-dotenv==1.0.0",
        "certifi==2023.7.22",
        "requests==2.31.0",
        "gradio-client==0.5.1",
    ],
)
