import setuptools


setuptools.setup(
    name='bs',
    version='1.0',
    description='List bugs and reviews in OpenStack projects',
    author='Rongze Zhu',
    author_email='zrzhit@gmail.com',
    url='http://github.com/zhurongze/bs',
    scripts=['bs.py'],
    install_requires=['paramiko', 'oslo.config'],
    py_modules=['bs'],
    entry_points={'console_scripts': ['bs = bs:main']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
)
