use strict;

#
# BEGIN spec
# "KBasePhenotype.PhenotypeSimulationSet-to-CSV": {
#   "cmd_args": {
#     "input": "-i",
#	  "workspace": "-w",
#     "output": "-o",
#     },
#     "cmd_description": "KBasePhenotype.PhenotypeSimulationSet to CSV",
#     "cmd_name": "trns_transform_KBasePhenotype.PhenotypeSimulationSet-to-CSV.pl",
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
my $wsclient = Bio::KBase::workspace::Client->new();
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
my $ret = $wsclient->get_objects([{ "ref" => $obj->{phenotypeset_ref} }]);
my $phenohash = {};
for (my $i=0; $i < @{$ret->[0]->{data}->{phenotypes}}; $i++) {
	$phenohash->{$ret->[0]->{data}->{phenotypes}->[$i]->{id}} = $ret->[0]->{data}->{phenotypes}->[$i];
}
my $tables = {$opt->workspace."_".$opt->input."_PhenotypeSimulations" => [["geneko","mediaws","media","addtlCpd","observed_growth","simulated_growth","simulated_growth_fraction","phenotype_class"]]};
for (my $i=0; $i < @{$obj->{phenotypeSimulations}}; $i++) {
	my $simpheno = $obj->{phenotypeSimulations}->[$i];
	my $array = [split(/\//,$simpheno->{phenotype_ref})];
	my $phenoid = pop(@{$array});
	my $pheno = $phenohash->{$phenoid};
	my $genekolist = $pheno->{geneko_refs};
	for (my $j=0; $j < @{$genekolist}; $j++) {
		my $array = [split(/\//,$genekolist->[$j])];
		$genekolist->[$j] = pop(@{$array}); 
	}
	my $cpdlist = $pheno->{additionalcompound_refs};
	for (my $j=0; $j < @{$cpdlist}; $j++) {
		my $array = [split(/\//,$cpdlist->[$j])];
		$cpdlist->[$j] = pop(@{$array}); 
	}
	my $output = $wsclient->get_object_info([{"ref" => $pheno->{media_ref}}],0);
	my $mediaws = $output->[0]->[7];
	my $media = $output->[0]->[1];
	push(@{$tables->{$opt->workspace."_".$opt->input."_PhenotypeSimulations"}},[join(";",@{$genekolist}),$mediaws,$media,join(";",@{$cpdlist}),$pheno->{normalizedGrowth},$simpheno->{simulatedGrowth},$simpheno->{simulatedGrowthFraction},$simpheno->{phenoclass}]);
}
write_csv_tables($tables);
