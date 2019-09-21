# Arxiv 2 Kindle PDF
arxiv2kindle_pdf: Recompiles an arxiv paper for kindle-sized screens.
This code heavily builds [on `bshillingford`'s code](https://gist.github.com/bshillingford/6259986edca707ca58dd).

# Usage

Provide the Arxiv's article ID or the URL as an argument, 
e.g. `
python arxiv2kindle_pdf.py -i=https://arxiv.org/abs/1508.06576
`.

Use `--help` to the get a complete list of arguments.

*optional* shell-executable 
   * Make executable: `chmod u+x arxiv2kindle_pdf.py`
   * Create a link in `~/bin`: `ln -s $PATH_TO_GIT/arxiv2kindle_pdf/arxiv2kindle_pdf.py ~/bin/arxiv2kindle_pdf`
   * Use from anywhere: `arxiv2kindle_pdf -i=https://arxiv.org/abs/1508.06576`

Note: Instructions and code are optimized for Linux / Unix usage.
