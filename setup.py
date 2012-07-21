from setuptools import setup

setup(
        name = "iron-mq",
        py_modules = ["iron_mq"],
        install_requires = ["iron_core"],
        version = "0.3",
        description = "Client library for IronMQ, a message queue in the cloud",
        author = "Iron.io",
        author_email = "thirdparty@iron.io",
        url = "https://github.com/iron-io/iron_mq_python",
        keywords = ["Iron.io", "IronMQ", "message", "queue", "MQ"],
        test_suite='test',
        classifiers = [
                "Programming Language :: Python",
                "Intended Audience :: Developers",
                "Operating System :: OS Independent",
                "License :: OSI Approved :: BSD License",
                "Natural Language :: English",
                "Topic :: Internet",
                "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        long_description = """\
IronMQ client library
---------------------

This package wraps the IronMQ API. It provides a simple and intuitive way
to interact with the IronMW service.

IronMQ is a service provided by Iron.io. A flexible, scalable,
and durable messaging system lets different parts of a cloud app
connect with and scale independently from other internal and external
processes. IronMQ offers developers ready-to-use messaging with reliable
delivery and cloud-optimized performance."""
)
