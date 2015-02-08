use strict;

#
# BEGIN spec
# "KBaseGenomes.Pangenome_to_Excel.Pangenome": {
#   "cmd_args": {
#     "input": "-i",
#	  "workspace": "-w",
#     "output": "-o",
#     },
#     "cmd_description": "KBaseGenomes.Pangenome to Excel",
#     "cmd_name": "trns_transform_KBaseGenomes_Pangenome_to_Excel_Pangenome.pl",
#     "max_runtime": 3600,
#     "opt_args": {
# 	 }
#   }
# }
# END spec
use JSON::XS;
use Getopt::Long::Descriptive;
use Bio::KBase::workspace::Client;
use Bio::KBase::Transform::ScriptHelpers qw(write_excel_tables write_csv_tables get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

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


my $obj;
my $wsclient = Bio::KBase::workspace::Client->new($opt->workspace_service_url);

my $ret = $wsclient->get_objects([{ name => $opt->object_name, workspace => $opt->workspace_name }])->[0];
if ($ret->{data})
{
    $obj = $ret->{data};
}
else
{
    die "Invalid return from get_object for ws=" . $opt->object_name . " input=" . $opt->object_name;
}

my $genomeHeaders = ["genome"];
my $familyHeaders = ["representative id","representative function","type","protein sequence"];
my $tables = {
	Genomes => [$genomeHeaders],
	Orthologs => [$familyHeaders]
};
my $wsinput = [];
my $wshash = {};
for (my $i=0; $i < @{$obj->{genome_refs}}; $i++) {
	push(@{$wsinput},{"ref" => $obj->{genome_refs}->[$i]});
	$wshash->{$obj->{genome_refs}->[$i]} = $i;
}
my $output = $wsclient->get_object_info($wsinput,0);
for (my $i=0; $i < @{$output}; $i++) {
	push(@{$genomeHeaders},$output->[$i]->[7]."/".$output->[$i]->[1]);
	push(@{$familyHeaders},$output->[$i]->[7]."/".$output->[$i]->[1]);
	my $row = [$output->[$i]->[7]."/".$output->[$i]->[1]];
	for (my $i=0; $i < @{$output}; $i++) {
		push(@{$row},0);	
	}
	push(@{$tables->{Genomes}},$row);
}
for (my $i=0; $i < @{$obj->{orthologs}}; $i++) {
	my $orthfam = $obj->{orthologs}->[$i];
	my $row = [
		$orthfam->{id},
		$orthfam->{function},
		$orthfam->{type},
		$orthfam->{protein_translation}
	];
	my $genomehash;
	for (my $j=0; $j < @{$orthfam->{orthologs}}; $j++) {
		$genomehash->{$orthfam->{orthologs}->[$j]->[2]} = $orthfam->{orthologs}->[$j]->[0].":".$orthfam->{orthologs}->[$j]->[1];
		for (my $k=0; $k < @{$orthfam->{orthologs}}; $k++) {
			$tables->{Genomes}->[1+$wshash->{$orthfam->{orthologs}->[$j]->[2]}]->[1+$wshash->{$orthfam->{orthologs}->[$k]->[2]}]++;
		}
	}
	for (my $j=0; $j < @{$obj->{genome_refs}}; $j++) {
		if (!defined($genomehash->{$obj->{genome_refs}->[$j]})) {
			push(@{$row},"");
		} else {
			push(@{$row},$genomehash->{$obj->{genome_refs}->[$j]});
		}
	}
	push(@{$tables->{Orthologs}},$row);
}
write_excel_tables($tables,$opt->workspace_name."_".$opt->object_name.".xls");
