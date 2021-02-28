#!/usr/bin/env node

const program = require('commander');
const cli = require('../src/cli').DynamicCreate;


program
    .command('[HTMLPath] [PDFPath]')
    .description('take as input zipped static html, outputs pdf in the given path')
    .action(function (HTMLPath, PDFPath) {
        if (process.argv.length !== 4) {
            program.help() //using commander for the auto generated help
        } else {
            let argv = process.argv;
            cli(argv[2], argv[3]);
        }
    })
    .parse(process.argv);
