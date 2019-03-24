import setuptools

with open("README.md", "r") as fh:

    long_description = fh.read()

setuptools.setup(

     name='youtube-curses',  

     version='0.1',

     scripts=['youtube-curses', 'img_display.py', 'query.py'] ,

     author="Marcelo V. Rozanti",

     author_email="mvrozanti@hotmail.com",

     description="YouTube browser built with ncurses",

     long_description=long_description,

     long_description_content_type="text/markdown",

     url="https://github.com/mvrozanti/youtube-curses",

     packages=setuptools.find_packages(),

     classifiers=[ ],

 )
