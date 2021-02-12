pdf_parse = require('@opendocsg/pdf2md')
fs = require('fs')

const pdfBuffer = fs.readFileSync(process.argv[2])
pdf_parse(pdfBuffer).then(text => {
    console.log(text)
}).catch(err => {
    console.error(err)
})