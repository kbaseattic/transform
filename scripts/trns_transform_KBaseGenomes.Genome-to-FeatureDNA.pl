use strict;

use JSON::XS;
use Getopt::Long::Descriptive;
use Bio::KBase::GenomeAnnotation::Client;
use Bio::KBase::Transform::ScriptHelpers qw(get_input_fh get_output_fh load_input write_output write_text_output);

#
# Use rast-export-genome to implement the transform. If -i / -o passed on command line
# these will pass to rast-export-genome to change input / output. Otherwise defaults to
# stdin / stdout.
#

my($opt, $usage) = describe_options("%c %o",
				    ['input|i=s', 'file from which the input is to be read'],
				    ['output|o=s', 'file to which the output is to be written'],
				    ['url=s', 'URL for the genome annotation service'],
				    );

my $genome = load_input($opt);



my $client = Bio::KBase::GenomeAnnotation::Client->new($opt->url);

my $formatted = $client->export_genome($genome, 'feature_dna', []);

write_text_output($formatted, $opt);
