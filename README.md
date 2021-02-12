# TTS any file

The goal is to **covert any file to spoken audio**.

Steps
 1. Convert any file to markdown (language independent)
 2. Convert markdown to ssml (czech only for now)
 3. Use a TTS engine to make audio out of ssml (language independent)

## installation
### Basic
#### venv
```
python3 -m venv ./venv
```
#### pip
```
pip install -r requirements.txt
```
#### Pandoc
[pandoc.org/installing](https://pandoc.org/installing.html)

#### FFmpeg
[ffmpeg.org/download.html](https://ffmpeg.org/download.html)
### Extras
#### pdf2md
```
npm i @opendocsg/pdf2md
```
OR
```
npm install
```
#### OCRmyPDF
[github.com/jbarlow83/OCRmyPDF](https://github.com/jbarlow83/OCRmyPDF#installation)

## Credits
### separator.py
Mgr. Petr Machovec [ROZDĚLOVAČ](https://nlp.fi.muni.cz/projekty/rozdelovac_vet/home.cgi)
### roman_num.py
Made out of a few code samples found on the internet.  
[roman numeral validator](https://stackoverflow.com/questions/267399/how-do-you-match-only-valid-roman-numerals-with-a-regular-expression)  
[roman numeral encoder](https://stackoverflow.com/questions/28777219/basic-program-to-convert-integer-to-roman-numerals)  
[roman numeral decoder](https://rosettacode.org/wiki/Roman_numerals/Decode)  

## Usage
```
./TTS\ File.py <path>
```