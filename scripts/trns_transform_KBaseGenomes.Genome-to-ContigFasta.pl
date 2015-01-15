use strict;

#
# BEGIN spec
# "KBaseGenomes.Genome-to-ContigFasta": {
#   "cmd_args": {
#     "input": "-i",
#     "output": "-o",
#     "genome_annotation_url": "--url",
#     },
#     "cmd_description": "KBaseGenomes.Genome to ContigFasta",
#     "cmd_name": "trns_transform_KBaseGenomes.Genome-to-ContigFasta.pl",
#     "max_runtime": 3600,
#     "opt_args": {
# 	 }
#   }
# }
# END spec
use JSON::XS;
use Getopt::Long::Descriptive;
use Bio::KBase::workspace::Client;
use Bio::KBase::GenomeAnnotation::Client;
use Bio::KBase::Transform::ScriptHelpers qw(get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

my($opt, $usage) = describe_options("%c %o",
				    ['input|i=s', 'workspace object id from which the input is to be read'],
				    ['workspace|w=s', 'workspace id from which the input is to be read'],
				    ['from-file', 'specifies to use the local filesystem instead of workspace'],
				    ['output|o=s', 'file to which the output is to be written'],
				    ['url=s', 'URL for the genome annotation service'],
				    ['help|h', 'show this help message'],
				    );

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

my $genome;

if ($opt->from_file)
{
    $genome = load_input($opt);
}
else
{
    if (!$opt->workspace)
    {
	die "A workspace name must be provided";
    }
    my $wsclient = Bio::KBase::workspace::Client->new();
    my $ret = $wsclient->get_object({ id => $opt->input, workspace => $opt->workspace });
    if ($ret->{data})
    {
	$genome = $ret->{data};
    }
    else
    {
	die "Invalid return from get_object for ws=" . $opt->workspace . " input=" . $opt->input;
    }
}
$genome = genome_to_gto($genome);

my $client = Bio::KBase::GenomeAnnotation::Client->new($opt->url);

my $formatted = $client->export_genome($genome, 'contig_fasta', []);

write_text_output($formatted, $opt);
