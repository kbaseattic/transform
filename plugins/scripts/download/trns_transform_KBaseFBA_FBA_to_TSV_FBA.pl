use strict;

# BEGIN spec
# "KBaseFBA_FBA_to_TSV_FBA": {
#   "cmd_args": {
#     "input": "-i",
#	  "workspace": "-w",
#     "output": "-o",
#     },
#     "cmd_description": "KBaseFBA.FBA to TSV",
#     "cmd_name": "trns_transform_KBaseFBA_FBA_to_TSV_FBA.pl",
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
<<<<<<< HEAD:plugins/scripts/download/trns_transform_KBaseFBA.FBA-to-CSV.pl
				    ['input_file_name|i=s', 'workspace object id from which the input is to be read'],
				    ['workspace_name|w=s', 'workspace id from which the input is to be read'],
				    ['from_file', 'specifies to use the local filesystem instead of workspace'],
				    ['url=s', 'URL for the genome annotation service'],
=======
				    ['object_name=s', 'workspace object name from which the input is to be read'],
				    ['workspace_name=s', 'workspace name from which the input is to be read'],
				    ['workspace_service_url=s', 'workspace service url to pull from'],
>>>>>>> 9d40e96dfcc4734be6bfd3ad79d9958b60233f3d:plugins/scripts/download/trns_transform_KBaseFBA_FBA_to_TSV_FBA.pl
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
<<<<<<< HEAD:plugins/scripts/download/trns_transform_KBaseFBA.FBA-to-CSV.pl
    if (!$opt->workspace_name)
    {
	die "A workspace name must be provided";
    }
    my $ret = $wsclient->get_object({ id => $opt->input_file_name, workspace => $opt->workspace_name });
    if ($ret->{data})
    {
	$obj = $ret->{data};
    }
    else
    {
	die "Invalid return from get_object for ws=" . $opt->workspace_name . " input=" . $opt->input_file_name;
    }
=======
    die "Invalid return from get_object for ws=" . $opt->workspace_name . " input=" . $opt->object_name;
>>>>>>> 9d40e96dfcc4734be6bfd3ad79d9958b60233f3d:plugins/scripts/download/trns_transform_KBaseFBA_FBA_to_TSV_FBA.pl
}

my $ret = $wsclient->get_objects([{ "ref" => $obj->{fbamodel_ref} }]);
my $cpdhash;
for (my $i=0; $i < @{$ret->[0]->{data}->{modelcompounds}}; $i++) {
	my $cpd = $ret->[0]->{data}->{modelcompounds}->[$i];
	$cpdhash->{$cpd->{id}} = $cpd;
	if ($cpd->{id} =~ m/(.+)_([a-z]\d+)$/) {
		my $id = $1;
		$cpd->{compartment} = $2;
		if ($cpd->{name} =~ m/(.+)_([a-z]\d+)$/) {
			$cpd->{name} = $1;
		}
	}
}
my $dirtrans = {
	">" => "=>",
	"<" => "<=",
	"=" => "<=>"
};
my $rxnhash;
for (my $i=0; $i < @{$ret->[0]->{data}->{modelreactions}}; $i++) {
	my $rxn = $ret->[0]->{data}->{modelreactions}->[$i];
	$rxnhash->{$rxn->{id}} = $rxn;
	my $array = [split(/\//,$rxn->{modelcompartment_ref})];
	$rxn->{compartment} = pop(@{$array});
	my $gpr = "Unknown";
	my $complexes = [];
	for (my $j=0; $j < @{$rxn->{modelReactionProteins}}; $j++) {
		my $subunits = [];
		for (my $k=0; $k < @{$rxn->{modelReactionProteins}->[$j]->{modelReactionProteinSubunits}}; $k++) {
			my $ftrs = [];
			for (my $m=0; $m < @{$rxn->{modelReactionProteins}->[$j]->{modelReactionProteinSubunits}->[$k]->{feature_refs}}; $m++) {
				my $array = [split(/\//,$rxn->{modelReactionProteins}->[$j]->{modelReactionProteinSubunits}->[$k]->{feature_refs}->[$m])];
				my $gene = pop(@{$array});
				push(@{$ftrs},$gene);
			}
			my $su = join(") or (",@{$ftrs});
			if (@{$ftrs} > 1) {
				$su = "(".$su.")";
			}
			push(@{$subunits},$su);
		}
		my $cpx = join(") and (",@{$subunits});
		if (@{$subunits} > 1) {
			$cpx = "(".$cpx.")";
		}
		push(@{$complexes},$cpx);
	}
	$gpr = join(") or (",@{$complexes});
	if (@{$complexes} > 1) {
		$gpr = "(".$gpr.")";
	}
	$rxn->{gpr} = $gpr;
	my $reactants;
	my $products;
	if (!defined($rxn->{pathway})) {
		$rxn->{pathway} = "Unknown";
	}
	for (my $j=0; $j < @{$rxn->{modelReactionReagents}}; $j++) {
		my $rgt = $rxn->{modelReactionReagents}->[$j];
		my $array = [split(/\//,$rgt->{modelcompound_ref})];
		my $cpd = pop(@{$array});
		my $rgtcmp = "c0";
		if ($cpd =~ m/(.+)_([a-z]\d+)$/) {
			$cpd = $1;
			$rgtcmp = $2;
		}
		if ($rgt->{coefficient} < 0) {
			if (length($reactants) > 0) {
				$reactants .= " + ";
			}
			$reactants .= "(".(-1*$rgt->{coefficient}).") ".$cpd."[".$rgtcmp."]";
		} else {
			if (length($products) > 0) {
				$products .= " + ";
			}
			$products .= "(".($rgt->{coefficient}).") ".$cpd."[".$rgtcmp."]";
		}
	}
	$rxn->{equation} = $reactants." ".$dirtrans->{$rxn->{direction}}." ".$products;
}
my $tables = {
<<<<<<< HEAD:plugins/scripts/download/trns_transform_KBaseFBA.FBA-to-CSV.pl
	$opt->workspace_name."_".$opt->input_file_name."_FBACompounds" => [["id","name","formula","charge","comopartment","uptake","min_uptake","lowerbound","max_uptake","upperbound"]],
	$opt->workspace_name."_".$opt->input_file_name."_FBAReactions" => [["id","direction","compartment","gpr","name","pathway","equation","flux","min_flux","lowerbound","max_flux","upperbound"]]
=======
	$opt->workspace_name."_".$opt->object_name."_FBACompounds" => [["id","name","formula","charge","comopartment","uptake","min_uptake","lowerbound","max_uptake","upperbound"]],
	$opt->workspace_name."_".$opt->object_name."_FBAReactions" => [["id","direction","compartment","gpr","name","pathway","equation","flux","min_flux","lowerbound","max_flux","upperbound"]]
>>>>>>> 9d40e96dfcc4734be6bfd3ad79d9958b60233f3d:plugins/scripts/download/trns_transform_KBaseFBA_FBA_to_TSV_FBA.pl
};
for (my $i=0; $i < @{$obj->{FBACompoundVariables}}; $i++) {
	my $var = $obj->{FBACompoundVariables}->[$i];
	my $array = [split(/\//,$var->{modelcompound_ref})];
	my $cpdid = pop(@{$array});
	my $cpd = $cpdhash->{$cpdid};
<<<<<<< HEAD:plugins/scripts/download/trns_transform_KBaseFBA.FBA-to-CSV.pl
	push(@{$tables->{$opt->workspace_name."_".$opt->input_file_name."_FBACompounds"}},[
=======
	push(@{$tables->{$opt->workspace_name."_".$opt->object_name."_FBACompounds"}},[
>>>>>>> 9d40e96dfcc4734be6bfd3ad79d9958b60233f3d:plugins/scripts/download/trns_transform_KBaseFBA_FBA_to_TSV_FBA.pl
		$cpdid,
		$cpd->{name},
		$cpd->{formula},
		$cpd->{charge},
		$cpd->{compartmnet},
		$var->{value},
		$var->{min},
		$var->{lowerBound},
		$var->{max},
		$var->{upperBound}
	]);
}
for (my $i=0; $i < @{$obj->{FBAReactionVariables}}; $i++) {
	my $var = $obj->{FBAReactionVariables}->[$i];
	my $array = [split(/\//,$var->{modelreaction_ref})];
	my $rxnid = pop(@{$array});
	my $rxn = $rxnhash->{$rxnid};
<<<<<<< HEAD:plugins/scripts/download/trns_transform_KBaseFBA.FBA-to-CSV.pl
	push(@{$tables->{$opt->workspace_name."_".$opt->input_file_name."_FBAReactions"}},[
=======
	push(@{$tables->{$opt->workspace_name."_".$opt->object_name."_FBAReactions"}},[
>>>>>>> 9d40e96dfcc4734be6bfd3ad79d9958b60233f3d:plugins/scripts/download/trns_transform_KBaseFBA_FBA_to_TSV_FBA.pl
		$rxnid,
		$dirtrans->{$rxn->{direction}},
		$rxn->{compartment},
		$rxn->{gpr},
		$rxn->{name},
		$rxn->{pathway},
		$rxn->{equation},
		$var->{value},
		$var->{min},
		$var->{lowerBound},
		$var->{max},
		$var->{upperBound}
	]);
}
write_csv_tables($tables);
