use strict;

# BEGIN spec
# "KBaseBiochem_Media_to_TSV_Media": {
#   "cmd_args": {
#     "input": "-i",
#     "output": "-o",
#     },
#     "cmd_description": "KBaseBiochem.Media to TSV",
#     "cmd_name": "trns_transform_KBaseBiochem_Media_to_TSV.pl",
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
				    ['object_version=s', 'workspace service url to pull from'],
				    ['help|h', 'show this help message']
);

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

if (!$opt->workspace_name)
{
    die "A workspace name must be provided";
}

my $obj;
my $wsclient = Bio::KBase::workspace::Client->new($opt->workspace_service_url);
my $ret;

if ($opt->object_version) {
    $ret = $wsclient->get_objects([{ name => $opt->object_name, workspace => $opt->workspace_name, ver => $opt->object_version}])->[0];
}
else {
    $ret = $wsclient->get_objects([{ name => $opt->object_name, workspace => $opt->workspace_name}])->[0];
}


if ($ret->{data})
{
    $obj = $ret->{data};
}
else
{
    die "Invalid return from get_object for ws=" . $opt->workspace_name . " input=" . $opt->object_name;
}

my $tables = {$opt->workspace_name."_".$opt->object_name."_Phenotypes" => [["geneko","mediaws","media","addtlCpd","growth"]]};
for (my $i=0; $i < @{$obj->{phenotypes}}; $i++) {
	my $genekolist = $obj->{phenotypes}->[$i]->{geneko_refs};
	for (my $j=0; $j < @{$genekolist}; $j++) {
		my $array = [split(/\//,$genekolist->[$j])];
		$genekolist->[$j] = pop(@{$array}); 
	}
	my $cpdlist = $obj->{phenotypes}->[$i]->{additionalcompound_refs};
	for (my $j=0; $j < @{$cpdlist}; $j++) {
		my $array = [split(/\//,$cpdlist->[$j])];
		$cpdlist->[$j] = pop(@{$array}); 
	}
	my $output = $wsclient->get_object_info([{"ref" => $obj->{phenotypes}->[$i]->{media_ref}}],0);
	my $mediaws = $output->[0]->[7];
	my $media = $output->[0]->[1];
	push(@{$tables->{$opt->workspace_name."_".$opt->object_name."_Phenotypes"}},[join(";",@{$genekolist}),$mediaws,$media,join(";",@{$cpdlist}),$obj->{phenotypes}->[$i]->{normalizedGrowth}]);
}
write_csv_tables($tables);
