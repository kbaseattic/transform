use strict;

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

#PERL USE
use JSON::XS;
use Getopt::Long::Descriptive;

#KBASE USE
use Bio::KBase::workspace::Client;
use Bio::KBase::Transform::ScriptHelpers qw(write_csv_tables get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

my($opt, $usage) = describe_options("%c %o",
				    ['object_name=s', 'workspace object name from which the input is to be read'],
				    ['workspace_name=s', 'workspace name from which the input is to be read'],
				    ['workspace_service_url=s', 'workspace service url to pull from'],
				    ['help|h', 'show this help message'],
);

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

if (!$opt->workspace_name)
{
    die "A workspace name must be provided";
}

my $wsclient = Bio::KBase::workspace::Client->new($opt->workspace_service_url);
my $ret = $wsclient->get_objects([{ name => $opt->object_name, workspace => $opt->workspace_name }])->[0];

my $obj;

if ($ret->{data})
{
    $obj = $ret->{data};
}
else
{
    die "Invalid return from get_object for ws=" . $opt->workspace_name . " input=" . $opt->object_name;
}

my $tables = {$opt->workspace_name."_".$opt->object_name."_MediaCompounds" => [["compounds","concentrations","minflux","maxflux"]]};
for (my $i=0; $i < @{$obj->{mediacompounds}}; $i++) {
	if ($obj->{mediacompounds}->[$i]->{compound_ref} =~ m/(cpd\d+)/) {
		push(@{$tables->{$opt->workspace_name."_".$opt->object_name."_MediaCompounds"}},[$1,$obj->{mediacompounds}->[$i]->{concentration},$obj->{mediacompounds}->[$i]->{minFlux},$obj->{mediacompounds}->[$i]->{maxFlux}]);
	}
}
write_csv_tables($tables);
