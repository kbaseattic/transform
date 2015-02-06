use strict;

# BEGIN spec
# "KBaseFBA_FBAModel_to_TSV_FBAModel": {
#   "cmd_args": {
#     "input": "-i",
#	  "workspace": "-w",
#     "output": "-o",
#     },
#     "cmd_description": "KBaseFBA.FBAModel to TSV",
#     "cmd_name": "trns_transform_KBaseFBA_FBAModel_to_TSV_FBAModel.pl",
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


my $obj;
my $wsclient = Bio::KBase::workspace::Client->new($opt->workspace_service_url);

my $ret = $wsclient->get_objects([{ name => $opt->object_name, workspace => $opt->workspace_name }])->[0];
if ($ret->{data})
{
    $obj = $ret->{data};
}
else
{
    die "Invalid return from get_object for ws=" . $opt->workspace_name . " input=" . $opt->object_name;
}

my $tables = {
	$opt->workspace_name."_".$opt->object_name."_FBAModelCompounds" => [["id","name","formula","charge","aliases"]],
	$opt->workspace_name."_".$opt->object_name."_FBAModelReactions" => [["id","direction","compartment","gpr","name","enzyme","pathway","reference","equation"]]
};
my $cpdhash;
for (my $i=0; $i < @{$obj->{modelcompounds}}; $i++) {
	my $cpd = $obj->{modelcompounds}->[$i];
	if ($cpd->{id} =~ m/(.+)_([a-z]\d+)$/) {
		my $id = $1;
		my $comp = $2;
		if ($cpd->{name} =~ m/(.+)_([a-z]\d+)$/) {
			$cpd->{name} = $1;
		}
		if (!defined($cpdhash->{$id})) {
			$cpdhash->{$id} = $cpd;
			push(@{$tables->{$opt->workspace_name."_".$opt->object_name."_FBAModelCompounds"}},[
				$id,
				$cpd->{name},
				$cpd->{formula},
				$cpd->{charge},
				join(";",@{$cpd->{aliases}})
			]);
		}
	}
}
my $dirtrans = {
	">" => "=>",
	"<" => "<=",
	"=" => "<=>"
};
for (my $i=0; $i < @{$obj->{modelreactions}}; $i++) {
	my $rxn = $obj->{modelreactions}->[$i];
	my $array = [split(/\//,$rxn->{modelcompartment_ref})];
	my $cmp = pop(@{$array});
	my $enyzme = "Unknown";
	for (my $j=0; $j < @{$rxn->{aliases}}; $j++) {
		if ($rxn->{aliases}->[$j] =~ m/^EC:(.+)/) {
			$enyzme = $1;
			last;
		}
	}
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
	my $reactants;
	my $products;
	if (!defined($rxn->{pathway})) {
		$rxn->{pathway} = "Unknown";
	}
	if (!defined($rxn->{reference})) {
		$rxn->{reference} = "None";
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
	my $equation = $reactants." ".$dirtrans->{$rxn->{direction}}." ".$products;
	push(@{$tables->{$opt->workspace_name."_".$opt->object_name."_FBAModelReactions"}},[
		$rxn->{id},
		$dirtrans->{$rxn->{direction}},
		$cmp,
		$gpr,
		$rxn->{name},
		$enyzme,
		$rxn->{pathway},
		$rxn->{reference},
		$equation
	]);
}
for (my $i=0; $i < @{$obj->{biomasses}}; $i++) {
	my $bio = $obj->{biomasses}->[$i];
	my $reactants;
	my $products;
	for (my $j=0; $j < @{$bio->{biomasscompounds}}; $j++) {
		my $rgt = $bio->{biomasscompounds}->[$j];
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
	my $equation = $reactants." => ".$products;
	push(@{$tables->{$opt->workspace_name."_".$opt->object_name."_FBAModelReactions"}},[
		$bio->{id},
		"=>",
		"c0",
		"None",
		"Biomass",
		"None",
		"Macromolecule biosynthesis",
		"None",
		$equation
	]);
}
write_csv_tables($tables);
