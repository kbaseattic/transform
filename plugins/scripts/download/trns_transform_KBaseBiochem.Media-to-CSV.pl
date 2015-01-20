use strict;

#
# BEGIN spec
# "KBaseBiochem.Media-to-CSV": {
#   "cmd_args": {
#     "input": "-i",
#     "output": "-o",
#     },
#     "cmd_description": "KBaseBiochem.Media to CSV",
#     "cmd_name": "trns_transform_KBaseBiochem.Media-to-CSV.pl",
#     "max_runtime": 3600,
#     "opt_args": {
# 	 }
#   }
# }
# END spec
use JSON::XS;
use Getopt::Long::Descriptive;
use Bio::KBase::workspace::Client;
use Bio::KBase::Transform::ScriptHelpers qw(write_csv_tables get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

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

my $obj;

if ($opt->from_file)
{
    $obj = load_input($opt);
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
	$obj = $ret->{data};
    }
    else
    {
	die "Invalid return from get_object for ws=" . $opt->workspace . " input=" . $opt->input;
    }
}
my $tables = {MediaCompounds => [["compounds","concentrations","minflux","maxflux"]]};
for (my $i=0; $i < @{$obj->{mediacompounds}}; $i++) {
	if ($obj->{mediacompounds}->[$i]->{compound_ref} =~ m/(cpd\d+)/) {
		push(@{$tables->{MediaCompounds}},[$1,$obj->{mediacompounds}->[$i]->{concentration},$obj->{mediacompounds}->[$i]->{minFlux},$obj->{mediacompounds}->[$i]->{maxFlux}]);
	}
}
write_csv_tables($tables);
