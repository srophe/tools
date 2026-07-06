# How to Use this Repository

This repository contains the following:
- NHSL Code Snippets (TEI): `NHSLCodeSnippets.xml`. Use to copy/paste individual elements and element chunks into existing NHSL TEI XML files
- NHSL Template (TEI): `NHSLTemplate.xml`. Use as a starting point for creating a new NHSL record. Follow the prompts in the XML comments to fill out the record with the requisite information.
- VS Code Snippets (JSON file): `vscode-snippets.json`. Code snippets that can be installed into VS Code to assist in creating NHSL elements and element chunks. See below for installation instructions.

# VS Code Snippets: Installation Instructions

(Based on https://code.visualstudio.com/docs/editing/userdefinedsnippets#_create-your-own-snippets).

1. From VS Code, open File > Preferences, or Code > Preferences on Mac. From this menu, sleect the "Configure Snippets" option.
    1. You can alternatively press `ctrl/cmd+shift+p` and search for "Snippets: Configure Snippets"
2. Search for "XML" and select it, which should open an "xml.json" file.
    1. This will install these extensions for any project (i.e., folder/directory/repo) that you open in VS Code. You can, alternatively, choose to create a "New snippets file for 'repo'", i.e. your current repository.
3. Copy and paste the contents of `vscode-snippets.json` into the `xml.json` file.
    1. In the unlikely case that you already have XML extensions set up, leave out the outermost `{}` characters when copying from `vscode-snippets.json`

You should now be able to use these code snippets by typing the "nhsl" or "syriaca" prefix, selecting the snippet you want, and pressing `tab` or `enter/return`.

# Using VS Code Snippets

1. Put your cursor where you want to insert a snippet
2. Begin by typing "nhsl" or "syriaca" (the latter is used for teiHeader elements such as the `titleStmt/editor`, `titleStmt/respStmt`, and `revisionDesc/change`). Select from the list the snippet you want to insert. Press `tab` or `enter/return` to insert the snippet.
3. Press `tab` to cycle through the information that you need to fill in. This information may be in the form of a placeholder text to replace, or a list of several options to choose from.
4. Pay attention to validation errors and make sure to address all errors before moving on to the next snippet.