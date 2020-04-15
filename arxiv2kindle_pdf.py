#!/usr/bin/env python

import argparse
import requests
import lxml.html as html
import re
import os
import glob
import tempfile


def yn_to_bool(yn):
    assert yn in ('y', 'n')
    return yn == 'y'


def get_args():
    parser = argparse.ArgumentParser(description="""Download and compile a 
    kidle-compatible version of PDF to a specified directory.
    Usage example: arxiv2kindle_pdf -i=https://arxiv.org/abs/1508.06576 -d=~/Documents/arxiv_pdfs/
    """ + "Debugging note: if fails with 'cp: cannot stat '/tmp/$RANDOM/arxiv.pdf': No such file or directory' "
          "and a few lines before that it says 'correct file: /tmp/$RANDOM/arxiv.tex', "
          "check /tmp/$RANDOM/arxiv.log for errors."
          "This often happens when dependencies are missing in the pdf build step")

    parser.add_argument(
        '-i', '--article_id', dest='article_id',
        help="The article's Arxiv's ID, e.g. --article_id=1909.00166v1",
        required=True
    )
    parser.add_argument(
        '-l', '--landscape', dest='landscape',
        help="PDF orientation. Accepts y for landscape or n for vertical. "
             "Default value is y. e.g. --landscape=y",
        default='y',
        choices=['y', 'n']
    )
    parser.add_argument(
        '-e', '--encoding', dest='encoding',
        help="Select the string encoding scheme. "
             "Default value is utf8, e.g. --encoding=windows-1255",
        default='utf8',
    )
    parser.add_argument(
        '-d', '--output_dir', dest='output_dir',
        help="Directory of the output PDF. "
             "Defalut value is Desktop (~/Desktop/), e.g. --output_dir=~/Desktop/",
        default='~/Desktop/'
    )
    parser.add_argument(
        '-o', '--open_pdf', dest='open_pdf',
        help="Open PDF file when done. Accepts y or n. "
             "Default value is n. e.g. --open_pdf=y",
        default='n',
        choices=['y', 'n']
    )

    args = parser.parse_args()
    # args, unknown = parser.parse_known_args()

    # convert to bool
    args.landscape = yn_to_bool(args.landscape)
    args.open_pdf = yn_to_bool(args.open_pdf)

    return args


def main():
    args = get_args()
    article_id = args.article_id
    landscape = args.landscape
    output_dir = args.output_dir
    open_pdf = args.open_pdf
    encoding = args.encoding

    # paper settings (decrease width/height to increase font)
    width = "6in"
    height = "4in"
    margin = "0.2in"
    # settings for latex geometry package:
    if landscape:
        geom_settings = dict(paperwidth=width, paperheight=height, margin=margin)
    else:
        geom_settings = dict(paperwidth=height, paperheight=width, margin=margin)

    arxiv_id = re.match(
        r'(http://.*?/)?(?P<id>\d{4}\.\d{4,5}(v\d{1,2})?)',
        article_id.replace('https', 'http')
    ).group('id')
    arxiv_abs = 'http://arxiv.org/abs/' + arxiv_id
    # arxiv_pdf = 'http://arxiv.org/pdf/' + arxiv_id
    arxiv_pgtitle = \
        html.fromstring(requests.get(arxiv_abs).text.encode(encoding=encoding)).xpath('/html/head/title/text()')[0]
    arxiv_title = re.sub(r'\s+', ' ', re.sub(r'^\[[^]]+\]\s*', '', arxiv_pgtitle), re.DOTALL)
    arxiv_title_scrubbed = re.sub('[^-_A-Za-z0-9]+', '_', arxiv_title, re.DOTALL)
    print(f'Detected article: {arxiv_title_scrubbed}.\n'
          f'Starting resources download.\n')

    d = tempfile.mkdtemp(prefix='arxiv2kindle_')
    url = 'http://arxiv.org/e-print/' + arxiv_id
    os.system(
        f"""wget -O {os.path.join(d, 'src.tar.gz')} --user-agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0" {url}"""
    )
    os.chdir(d)  # change current dir
    os.system('tar xvf src.tar.gz')

    texfiles = glob.glob(os.path.join(d, '*.tex'))
    for texfile in texfiles:
        with open(texfile, 'r') as f:
            src = f.readlines()
        if 'documentclass' in src[0]:
            print('correct file: ' + texfile)
            break

    # filter comments/newlines for easier debugging:
    src = [line for line in src if line[0] != '%' and len(line.strip()) > 0]

    # strip font size, column stuff, and paper size stuff in documentclass line:
    src[0] = re.sub(r'\b\d+pt\b', '', src[0])
    src[0] = re.sub(r'\b\w+column\b', '', src[0])
    src[0] = re.sub(r'\b\w+paper\b', '', src[0])
    src[0] = re.sub(r'(?<=\[),', '', src[0])  # remove extraneous starting commas
    src[0] = re.sub(r',(?=[\],])', '', src[0])  # remove extraneous middle/ending commas

    # find begin{document}:
    begindocs = [i for i, line in enumerate(src) if line.startswith(r'\begin{document}')]
    assert (len(begindocs) == 1)
    src.insert(begindocs[0],
               '\\usepackage[' + ','.join(k + '=' + v for k, v in geom_settings.items()) + ']{geometry}\n')
    src.insert(begindocs[0], '\\usepackage{times}\n')
    src.insert(begindocs[0], '\\pagestyle{empty}\n')
    if landscape:
        src.insert(begindocs[0], '\\usepackage{pdflscape}\n')

    # shrink figures to be at most the size of the page:
    for i in range(len(src)):
        line = src[i]
        m = re.search(r'\\includegraphics\[width=([.\d]+)\\(line|text)width\]', line)
        if m:
            mul = m.group(1)
            src[i] = re.sub(r'\\includegraphics\[width=([.\d]+)\\(line|text)width\]',
                            r'\\includegraphics[width={mul}\\textwidth,height={mul}\\textheight,keepaspectratio]'.format(
                                mul=mul),
                            line)

    textout = os.popen(
        " && ".join([f"pdflatex --interaction=nonstopmode {texfile}"] * 3)
    ).readlines()
    print(textout[-8:])

    pdffilename = texfile[:-4] + '.pdf'
    os.system(f'''cp {pdffilename} {os.path.join(output_dir, arxiv_title_scrubbed + '.pdf')}''')

    if open_pdf:
        os.system('xdg-open ' + pdffilename)


if __name__ == '__main__':
    main()
