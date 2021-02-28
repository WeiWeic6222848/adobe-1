/*
 * Copyright 2019 Adobe
 * All Rights Reserved.
 *
 * NOTICE: Adobe permits you to use, modify, and distribute this file in
 * accordance with the terms of the Adobe license agreement accompanying
 * it. If you have received this file from a source other than Adobe,
 * then your use, modification, or distribution of it requires the prior
 * written permission of Adobe.
 */

const fs = require('fs');
const StreamZip = require('node-stream-zip');
const path = require('path');
const DCServicesSdk = require('@adobe/dc-services-node-sdk');

function Create(HTMLPath, PDFPath) {
  /**
     * sample function taken from demo-repo with a little adjustment
     * to let it be able to find the keys when called everywhere.
     */

  const setCustomOptions = (htmlToPDFOperation) => {
    // Define the page layout, in this case an 8.25 x 11.25 inch page (A4 portrait).
    const pageLayout = new DCServicesSdk.CreatePDF.options.PageLayout();
    pageLayout.setPageSize(11.75, 8.25);

    // Set the desired HTML-to-PDF conversion options.
    const htmlToPdfOptions = new DCServicesSdk.CreatePDF.options.html.CreatePDFFromHtmlOptions
      .Builder()
      .includesHeaderFooter(false)
      .withPageLayout(pageLayout)
      .build();
    htmlToPDFOperation.setOptions(htmlToPdfOptions);
  };
  try {
    // Initial setup, create credentials instance.
    const credentials = DCServicesSdk.Credentials
      .serviceAccountCredentialsBuilder()
      .fromFile(path.join(__dirname, '..', 'dc-services-sdk-credentials.json')) // finding the credentials in the relative, parent folder.
      .build();

    // Create an ExecutionContext using credentials and create a new operation instance.
    const executionContext = DCServicesSdk.ExecutionContext.create(credentials);
    const htmlToPDFOperation = DCServicesSdk.CreatePDF.Operation.createNew();

    // Set operation input from a source file.
    const input = DCServicesSdk.FileRef.createFromLocalFile(HTMLPath);
    htmlToPDFOperation.setInput(input);

    // Provide any custom configuration options for the operation.
    setCustomOptions(htmlToPDFOperation);

    // Execute the operation and Save the result to the specified location.
    htmlToPDFOperation.execute(executionContext)
      .then((result) => result.saveAsFile(PDFPath))
      .catch((err) => {
        if (err instanceof DCServicesSdk.Error.ServiceApiError
                    || err instanceof DCServicesSdk.Error.ServiceUsageError) {
          console.log('Exception encountered while executing operation', err);
        } else {
          console.log('Exception encountered while executing operation', err);
        }
      });
  } catch (err) {
    console.log('Exception encountered while executing operation', err);
  }
}

function Validate(HTMLPath, PDFPath) {
  // if the output file exists, overwrite.
  if (fs.existsSync(PDFPath)) {
    fs.unlinkSync(PDFPath);

    Create(HTMLPath, PDFPath);
  } else {
    // iff the input param will not cause a error, proceed to create HTML.
    Create(HTMLPath, PDFPath);
  }
}

function DynamicCreate(HTMLPath, PDFPath) {
  try {
    // check if input is a zip file
    // if the filename length is less than 4 or doesn't end with .zip, then it's not a zip file
    if (HTMLPath.substr(HTMLPath.length - 4) !== '.zip' || HTMLPath < 4) {
      throw new Error('Provided file is not an zip file!');
    }

    if (fs.existsSync(HTMLPath)) {
      // try to search index.html inside the zip
      const zip = new StreamZip({
        file: HTMLPath,
        storeEntries: true,
      });

      zip.on('error', (err) => {
        console.log(`Unable to unzip the file ${HTMLPath} : `, err);
      });

      zip.on('ready', () => {
        try {
          let found = false;
          // look at the files, and see if index.html is present.
          for (const entry of Object.values(zip.entries())) {
            if (`${entry.name}` === 'index.html') {
              found = true;
            }
          }

          if (!found) {
            // handle no index error.
            throw new Error('provided zip file does not contain an index.html!');
          }
          zip.close();
          Validate(HTMLPath, PDFPath);
        } catch (err) {
          console.log('Exception encountered while executing operation : ', err);
        }
      });
    } else {
      throw new Error("provided zip file doesn't exist!");
    }
  } catch (err) {
    console.log('Exception encountered while executing operation : ', err);
  }
}

module.exports = { DynamicCreate };
