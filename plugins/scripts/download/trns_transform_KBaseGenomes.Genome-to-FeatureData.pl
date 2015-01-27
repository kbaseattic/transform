use strict;
use Data::Dumper;
use JSON::XS;
use Getopt::Long::Descriptive;
use Bio::KBase::workspace::Client;
use Bio::KBase::GenomeAnnotation::Client;
use Bio::KBase::Transform::ScriptHelpers qw(get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

my($opt, $usage) = describe_options("%c %o",
				    ['workspace_service_url=s', 'Workspace URL'],
				    ['workspace_name=s', 'Workspace name', { required => 1 }],
				    ['object_name=s', 'Object name', { required => 1 }],
				    ['output_file_name=s', 'Output file name'],
				    ['working_directory=s', 'Output directory for generated files', { required => 1 }],
				    ['object_version', 'Workspace object version'],
				    ['genome_annotation_service_url=s', 'URL for the genome annotation service'],
				    ['help|h', 'show this help message'],
				   );

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

if (! -d $opt->working_directory)
{
    die "Specified working directory " . $opt->working_directory . " does not exist\n";
}

my $genome;

my $wsclient = Bio::KBase::workspace::Client->new($opt->workspace_service_url);
my $ret = $wsclient->get_objects([{
    workspace => $opt->workspace_name,
    name => $opt->object_name,
    (defined($opt->object_version) ? (ver => $opt->object_version) : ()),
}]);

if (!(ref($ret) eq 'ARRAY' && @$ret && $ret->[0]->{data}))
{
    die sprintf("Workspace did not return an object for %s in %s at %s\n", $opt->object_name, $opt->workspace_name, $opt->workspace_service_url);
}

my $genome = $ret->[0]->{data};

$genome = genome_to_gto($genome);

my $client = Bio::KBase::GenomeAnnotation::Client->new($opt->genome_annotation_service_url);

my $formatted = $client->export_genome($genome, 'feature_data', []);

my $out_file = $opt->output_file_name;
if (!$out_file)
{
    $out_file = join(".", $opt->object_name, 'txt');
}

if ($out_file =~ m,^/,)
{
    warn "Output file was specified using an absolute path; not prepending working directory";
}
else
{
    $out_file = $opt->working_directory . "/$out_file";
}

if (open(my $fh, ">", $out_file))
{
    print $fh $formatted;
    close($fh) or die "Error closing output file $out_file: $!";
}
else
{
    die "Error opening output file $out_file: $!";
}
