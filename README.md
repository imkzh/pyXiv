# pyXiv
Command line arXiv interface powered by python: http://arxiv.org/help/api/index
## About arXiv
Started in August 1991, [arXiv](http://arxiv.org/) is a project by the Cornell University Library that provides open 
access to 1,000,000+ articles. arXiv.org (formerly xxx.lanl.gov) is a highly-automated electronic archive and
distribution server for research articles. Covered areas include physics, mathematics, computer science,
nonlinear sciences, quantitative biology, quantitative finance, statistics, electrical engineering and systems science, 
and economics. arXiv is maintained and operated by the Cornell University Library with guidance from the arXiv 
Scientific Advisory Board and the arXiv Member Advisory Board, and with the help of numerous subject moderators.

## Todo lists:
* complete subcommand search
* complete subcommand query
* complete subcommand list
* complete subcommand show
* add support for OAI-PMH

# How to use it:

To get help, type:
    
    arxiv.py help

pyXiv allows you to download arXiv documents with its ID:

    arxiv.py download 1807.05705

or by title:
    
    arxiv.py download EIE
    
also, download multiple article at once is supported with download command, but remember to play nice:
    
    arxiv.py download 1807.05705 "EIE: Efficient Inference Engine" 1809.00001
