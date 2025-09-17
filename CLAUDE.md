# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Genonaut is a project to implement recommender systems for generative AI that can perpetually produce content (text, 
image, video, audio) based on user preferences.

## How to familiarize yourself with the project
- Read the README.md file in the root of the repository

## Code / architecture style
- Whenever possible, functions / methods should be pure functions.
- Use types often, especially for all function / method parameters.

## Standard Operating Procedures
### Common steps to do whenever creating/updating any task / feature
1. Add end-to-end tests.
2. Add unit tests for any functions/methods.
3. Add documentation: Module level docstrings, class level docstrings, function level docstrings, and method / function
level docstrings. Function / method docstrings should include information about parameters and returns, and a 
description. 
4. Periodic code commenting. For example, for a function that has several distinct steps, where each step involves a 
block of code (e.g. a `for` loop with several operations), put at least 1 comment above eaach block, explaining what it 
does. 
5. Ensure that the whole test suite passes before completion of a feature or major task.
6. If any new Python requirements / packages are added to the project, include them (unversioned) in the 
`requirements-unlocked.txt` file.
7. If the new feature has a CLI, document it in a "Features" section in the `README.md`. Include a table showing the 
args, their description, defaults, data types, etc.
8. Consider otherwise any other documentation that might need to be added or updated in `README.md` after adding a 
feature, and either do those updates or ask for input.
