use strict;

#
# BEGIN spec
# "KBaseGenomes.Genome-to-GFF": {
#   "cmd_args": {
#     "input": "-i",
#     "output": "-o",
#     "genome_annotation_url": "--url",
#     },
#     "cmd_description": "KBaseGenomes.Genome to GFF",
#     "cmd_name": "trns_transform_KBaseGenomes.Genome-to-GFF.pl",
#     "max_runtime": 3600,
#     "opt_args": {
# 	 }
#   }
# }
# END spec
use JSON::XS;
use Getopt::Long::Descriptive;
use Bio::KBase::GenomeAnnotation::Client;
use Bio::KBase::Transform::ScriptHelpers qw(get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

my($opt, $usage) = describe_options("%c %o",
				    ['input|i=s', 'file from which the input is to be read'],
				    ['output|o=s', 'file to which the output is to be written'],
				    ['url=s', 'URL for the genome annotation service'],
				    );

my $genome = load_input($opt);
$genome = genome_to_gto($genome);

my $client = Bio::KBase::GenomeAnnotation::Client->new($opt->url);

my $formatted = $client->export_genome($genome, 'gff', []);

write_text_output($formatted, $opt);
