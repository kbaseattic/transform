#!/usr/bin/env Rscript

my_function = function(data){
}

# argument parsing
suppressPackageStartupMessages(library("optparse"))
option_list = list( 
  make_option(c("-i", "--input"), dest = "file_name", type = "character", 
              help = "REQUIRED: Input file"), 
  make_option(c("-m", "--method"), type = "character", default = 'method', 
              help = "Method. [default \"%default\"]"), 
  make_option(c("-p", "--p_threshold"), type = "double", default = 0.05,
              help = "Maximum cut_off  [default %default]"), 
  make_option(c("-n", "--count"), type = "integer", default = 0,
              help = "Number [default %default]"),
  make_option(c("-o", "--output"), dest = "outFileName", type = "character",
              default = "out.txt", 
              help = "Output file  [default \"%default\"]") 
)

# pass arguments
description_text = "\nDESCRIPTION
\n\tThis function is an example r script 
\nInput: a file
\nOutput: a file"
usage_text = "\nNAME
\n\tmys_example -- my service example
\nSYNOPSIS
\n\t%prog [-impno]"
epilogue_text = "\nEXAMPLES 
\n\t$mys_example -i input.txt –m method -p 0.01 -o out.txt 
\nSEE ALSO 
\n\tcoex_net 
\n\tcoex_cluster 
\n\tcoex_cluster2
\nAUTHORS 
\n\tYour Name\n"
opt_obj = OptionParser(usage=usage_text,option_list=option_list,description=description_text,epilogue=epilogue_text)
opt = parse_args(opt_obj, print_help_and_exit = FALSE)
file_name = opt$file_name
method = opt$method
p_threshold = opt$p_threshold
count = opt$count
outFileName = opt$outFileName
if (opt$help) {
  print_help(opt_obj)
  quit(status = 0)
}

# prepare data
options(stringsAsFactors = FALSE)
if (is.null(file_name)) { stop("please give your input file name $./mys_example -i [your input file name]") }
#data = as.data.frame(read.csv(file_name, header = TRUE, row.names = 1, stringsAsFactors = FALSE))

# Running the function
my_function("")
