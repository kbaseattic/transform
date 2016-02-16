use strict;

# BEGIN spec
# "KBaseFBA.FBAModel-to-SBML": {
#   "cmd_args": {
#     "input": "-i",
#	  "workspace": "-w",
#     "output": "-o",
#     },
#     "cmd_description": "KBaseFBA.FBAModel to SBML",
#     "cmd_name": "trns_transform_KBaseFBA.FBAModel-to-SBML.pl",
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
use Bio::KBase::Transform::ScriptHelpers qw(getStderrLogger write_csv_tables get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

my($opt, $usage) = describe_options("%c %o",
				    ['object_name=s', 'workspace object name from which the input is to be read'],
				    ['workspace_name=s', 'workspace name from which the input is to be read'],
				    ['workspace_service_url=s', 'workspace service url to pull from'],
				    ['help|h', 'show this help message'],
				    );

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

my $logger = getStderrLogger();
$logger->info("Generating SBML for WS model");

my $output;
use Capture::Tiny qw( capture );
my ($stdout, $stderr, @result) = capture {
    my $wsclient = Bio::KBase::workspace::Client->new($opt->workspace_service_url);
    my $ret = $wsclient->get_objects([{ name => $opt->object_name, workspace => $opt->workspace_name }])->[0];
	
	my $obj;
	if ($ret->{data}) {
	    $obj = $ret->{data};
	} else {
	    die "Invalid return from get_object for ws=" . $opt->workspace_name . " input=" . $opt->object_name;
	}
	#Translating model ID to ID that is compatible with SBML
	my $modelid = $opt->object_name;
	# SIds must begin with a letter
	$modelid =~ s/^([^a-zA-Z])/Mdl_$1/;
    # SIDs must only contain letters numbers or '_'
    $modelid =~ s/[^a-zA-Z0-9_]/_/g;
	#Printing header to SBML file
	$output = [];
	push(@{$output},'<?xml version="1.0" encoding="UTF-8"?>');
	push(@{$output},'<sbml xmlns="http://www.sbml.org/sbml/level2" level="2" version="1" xmlns:html="http://www.w3.org/1999/xhtml">');
	my $name = $opt->object_name." KBase model";
	$name =~ s/[\s\.]/_/g;
	push(@{$output},'<model id="'.$modelid.'" name="'.$name.'">');

	#Printing the unit data
	push(@{$output},"<listOfUnitDefinitions>");
	push(@{$output},"\t<unitDefinition id=\"mmol_per_gDW_per_hr\">");
	push(@{$output},"\t\t<listOfUnits>");
	push(@{$output},"\t\t\t<unit kind=\"mole\" scale=\"-3\"/>");
	push(@{$output},"\t\t\t<unit kind=\"gram\" exponent=\"-1\"/>");
	push(@{$output},"\t\t\t<unit kind=\"second\" multiplier=\".00027777\" exponent=\"-1\"/>");
	push(@{$output},"\t\t</listOfUnits>");
	push(@{$output},"\t</unitDefinition>");
	push(@{$output},"</listOfUnitDefinitions>");

	#Printing compartments for SBML file
	push(@{$output},'<listOfCompartments>');
	for (my $i=0; $i < @{$obj->{modelcompartments}}; $i++) {
		my $cmp = $obj->{modelcompartments}->[$i];
    	push(@{$output},'<compartment '.&CleanNames("id",$cmp->{id}).' '.&CleanNames("name",$cmp->{label}).' />');
    }
	push(@{$output},'</listOfCompartments>');
	#Printing the list of metabolites involved in the model
	push(@{$output},'<listOfSpecies>');
	for (my $i=0; $i < @{$obj->{modelcompounds}}; $i++) {
		my $cpd = $obj->{modelcompounds}->[$i];
		$cpd->{msid} = $cpd->{reaction_ref};
		$cpd->{msid} =~ s/.+\///g;
		$cpd->{msid} =~ s/_.+//g;
		if ($cpd->{msid} eq "cpd00000") {
			$cpd->{msid} = $cpd->{id};
			$cpd->{msid} =~ s/_.+//g;
		}
		$cpd->{cmplabel} = "c0";
		if ($cpd->{id} =~ m/_([a-z]+\d+)^/) {
			$cpd->{cmplabel} = $1;
		}	
		push(@{$output},'<species '.&CleanNames("id",$cpd->{id}).' '.&CleanNames("name",$cpd->{name}).' compartment="'.$cpd->{cmplabel}.'" charge="'.$cpd->{charge}.'" boundaryCondition="false"/>');
		if ($cpd->{msid} eq "cpd11416" || $cpd->{msid} eq "cpd15302" || $cpd->{msid} eq "cpd08636") {
			push(@{$output},'<species '.&CleanNames("id",$cpd->{msid}."_b").' '.&CleanNames("name",$cpd->{name}."_b").' compartment="'.$cpd->{cmplabel}.'" charge="'.$cpd->{charge}.'" boundaryCondition="true"/>');
		}
	}
	for (my $i=0; $i < @{$obj->{modelcompounds}}; $i++) {
		my $cpd = $obj->{modelcompounds}->[$i];
		if ($cpd->{cmplabel} =~ m/^e/) {
			push(@{$output},'<species '.&CleanNames("id",$cpd->{msid}."_b").' '.&CleanNames("name",$cpd->{name}."_b").' compartment="'.$cpd->{cmplabel}.'" charge="'.$cpd->{charge}.'" boundaryCondition="true"/>');
		}
	}
	push(@{$output},'</listOfSpecies>');
	push(@{$output},'<listOfReactions>');
	my $mdlrxns = $obj->{modelreactions};
	for (my $i=0; $i < @{$mdlrxns}; $i++) {
		my $rxn = $mdlrxns->[$i];
		$rxn->{gprString} = "Unknown";
		my $complexarray = [];
		if (defined($rxn->{modelReactionProteins})) {
			for (my $k=0; $k < @{$rxn->{modelReactionProteins}}; $k++) {
				my $subybunitarray = [];
				if (defined($rxn->{modelReactionProteins}->[$k]->{modelReactionProteinSubunits})) {
					for (my $j=0; $j < @{$rxn->{modelReactionProteins}->[$k]->{modelReactionProteinSubunits}}; $j++) {
						my $featurearray = [];
						if (defined($rxn->{modelReactionProteins}->[$k]->{modelReactionProteinSubunits}->[$j]->{feature_refs})) {
							for (my $m=0; $m < @{$rxn->{modelReactionProteins}->[$k]->{modelReactionProteinSubunits}->[$j]->{feature_refs}}; $m++) {
								my $ftr = $rxn->{modelReactionProteins}->[$k]->{modelReactionProteinSubunits}->[$j]->{feature_refs}->[$m];
								$ftr =~ s/.+\///g;
								push(@{$featurearray},$ftr);
							}
						}
						if (@{$featurearray} > 0) {
							push(@{$subybunitarray},"(".join(" or ",@{$featurearray}).")");
						}
					}
				}
				if (@{$subybunitarray} > 0) {
					push(@{$complexarray},"(".join(" and ",@{$subybunitarray}).")");
				}
			}
		}
		if (@{$complexarray} > 0) {
			$rxn->{gprString} = "(".join(" or ",@{$complexarray}).")";
		}
		my $reversibility = "true";
		my $lb = -1000;
		if ($rxn->{direction} ne "=") {
			$lb = 0;
			$reversibility = "false";
		}
		push(@{$output},'<reaction '.&CleanNames("id",$rxn->{id}).' '.&CleanNames("name",$rxn->{name}).' '.&CleanNames("reversible",$reversibility).'>');
		push(@{$output},"<notes>");
		my $GeneAssociation = $rxn->{gprString};
		my $ProteinAssociation = $rxn->{gprString};
		push(@{$output},"<html:p>GENE_ASSOCIATION:".$GeneAssociation."</html:p>");
		push(@{$output},"<html:p>PROTEIN_ASSOCIATION:".$ProteinAssociation."</html:p>");
		push(@{$output},"</notes>");
		my $firstreact = 1;
		my $firstprod = 1;
		my $prodoutput = [];
		my $rgts = $rxn->{modelReactionReagents};
		my $sign = 1;
		if ($rxn->{direction} eq "<") {
			$sign = -1;
		}
		for (my $j=0; $j < @{$rgts}; $j++) {
			my $rgt = $rgts->[$j];
			$rgt->{id} = $rgt->{modelcompound_ref};
			$rgt->{id} =~ s/.+\///g;
			if ($sign*$rgt->{coefficient} < 0) {
				if ($firstreact == 1) {
					$firstreact = 0;
					push(@{$output},"<listOfReactants>");
				}
				push(@{$output},'<speciesReference '.&CleanNames("species",$rgt->{id}).' stoichiometry="'.-1*$sign*$rgt->{coefficient}.'"/>');	
			} else {
				if ($firstprod == 1) {
					$firstprod = 0;
					push(@{$prodoutput},"<listOfProducts>");
				}
				push(@{$prodoutput},'<speciesReference '.&CleanNames("species",$rgt->{id}).' stoichiometry="'.$sign*$rgt->{coefficient}.'"/>');
			}
		}
		if ($firstreact != 1) {
			push(@{$output},"</listOfReactants>");
		}
		if ($firstprod != 1) {
			push(@{$prodoutput},"</listOfProducts>");
		}
		push(@{$output},@{$prodoutput});
		push(@{$output},"<kineticLaw>");
		push(@{$output},"\t<math xmlns=\"http://www.w3.org/1998/Math/MathML\">");
		push(@{$output},"\t\t\t<ci> FLUX_VALUE </ci>");
		push(@{$output},"\t</math>");
		push(@{$output},"\t<listOfParameters>");
		push(@{$output},"\t\t<parameter id=\"LOWER_BOUND\" value=\"".$lb."\" name=\"mmol_per_gDW_per_hr\"/>");
		push(@{$output},"\t\t<parameter id=\"UPPER_BOUND\" value=\"1000\" name=\"mmol_per_gDW_per_hr\"/>");
		push(@{$output},"\t\t<parameter id=\"OBJECTIVE_COEFFICIENT\" value=\"0\"/>");
		push(@{$output},"\t\t<parameter id=\"FLUX_VALUE\" value=\"0.0\" name=\"mmol_per_gDW_per_hr\"/>");
		push(@{$output},"\t</listOfParameters>");
		push(@{$output},"</kineticLaw>");
		push(@{$output},'</reaction>');
	}
	my $bios = $obj->{biomasses};
	for (my $i=0; $i < @{$bios}; $i++) {
		my $rxn = $bios->[$i];
		my $objective = 0;
		if ($i==0) {
			$objective = 1;
		}
		my $reversibility = "false";
		push(@{$output},'<reaction '.&CleanNames("id","biomass".$i).' '.&CleanNames("name",$rxn->{name}).' '.&CleanNames("reversible",$reversibility).'>');
		push(@{$output},"<notes>");
		push(@{$output},"<html:p>GENE_ASSOCIATION: </html:p>");
		push(@{$output},"<html:p>PROTEIN_ASSOCIATION: </html:p>");
		push(@{$output},"<html:p>SUBSYSTEM: </html:p>");
		push(@{$output},"<html:p>PROTEIN_CLASS: </html:p>");
		push(@{$output},"</notes>");
		my $firstreact = 1;
		my $firstprod = 1;
		my $prodoutput = [];
		my $biocpds = $rxn->{biomasscompounds};
		for (my $j=0; $j < @{$biocpds}; $j++) {
			my $rgt = $biocpds->[$j];
			$rgt->{id} = $rgt->{modelcompound_ref};
			$rgt->{id} =~ s/.+\///g;
			if ($rgt->{coefficient} < 0) {
				if ($firstreact == 1) {
					$firstreact = 0;
					push(@{$output},"<listOfReactants>");
				}
				push(@{$output},'<speciesReference '.&CleanNames("species",$rgt->{id}).' stoichiometry="'.-1*$rgt->{coefficient}.'"/>');	
			} else {
				if ($firstprod == 1) {
					$firstprod = 0;
					push(@{$prodoutput},"<listOfProducts>");
				}
				push(@{$prodoutput},'<speciesReference '.&CleanNames("species",$rgt->{id}).' stoichiometry="'.$rgt->{coefficient}.'"/>');
			}
		}
		if ($firstreact != 1) {
			push(@{$output},"</listOfReactants>");
		}
		if ($firstprod != 1) {
			push(@{$prodoutput},"</listOfProducts>");
		}
		push(@{$output},@{$prodoutput});
		push(@{$output},"<kineticLaw>");
		push(@{$output},"\t<math xmlns=\"http://www.w3.org/1998/Math/MathML\">");
		push(@{$output},"\t\t\t<ci> FLUX_VALUE </ci>");
		push(@{$output},"\t</math>");
		push(@{$output},"\t<listOfParameters>");
		push(@{$output},"\t\t<parameter id=\"LOWER_BOUND\" value=\"0.0\" name=\"mmol_per_gDW_per_hr\"/>");
		push(@{$output},"\t\t<parameter id=\"UPPER_BOUND\" value=\"1000\" name=\"mmol_per_gDW_per_hr\"/>");
		push(@{$output},"\t\t<parameter id=\"OBJECTIVE_COEFFICIENT\" value=\"".$objective."\"/>");
		push(@{$output},"\t\t<parameter id=\"FLUX_VALUE\" value=\"0.0\" name=\"mmol_per_gDW_per_hr\"/>");
		push(@{$output},"\t</listOfParameters>");
		push(@{$output},"</kineticLaw>");
		push(@{$output},'</reaction>');
	}
	my $cpds = $obj->{modelcompounds};
	for (my $i=0; $i < @{$cpds}; $i++) {
		my $cpd = $cpds->[$i];
		my $lb = -1000;
		my $ub = 1000;
		if ($cpd->{cmplabel} =~ m/^e/ || $cpd->{msid} eq "cpd08636" || $cpd->{msid} eq "cpd11416" || $cpd->{msid} eq "cpd15302") {
			push(@{$output},'<reaction '.&CleanNames("id",'EX_'.$cpd->{id}).' '.&CleanNames("name",'EX_'.$cpd->{name}).' reversible="true">');
			push(@{$output},"\t".'<notes>');
			push(@{$output},"\t\t".'<html:p>GENE_ASSOCIATION: </html:p>');
			push(@{$output},"\t\t".'<html:p>PROTEIN_ASSOCIATION: </html:p>');
			push(@{$output},"\t\t".'<html:p>PROTEIN_CLASS: </html:p>');
			push(@{$output},"\t".'</notes>');
			push(@{$output},"\t".'<listOfReactants>');
			push(@{$output},"\t\t".'<speciesReference '.&CleanNames("species",$cpd->{id}).' stoichiometry="1.000000"/>');
			push(@{$output},"\t".'</listOfReactants>');
			push(@{$output},"\t".'<listOfProducts>');
			push(@{$output},"\t\t".'<speciesReference '.&CleanNames("species",$cpd->{msid}."_b").' stoichiometry="1.000000"/>');
			push(@{$output},"\t".'</listOfProducts>');
			push(@{$output},"\t".'<kineticLaw>');
			push(@{$output},"\t\t".'<math xmlns="http://www.w3.org/1998/Math/MathML">');
			push(@{$output},"\t\t\t\t".'<ci> FLUX_VALUE </ci>');
			push(@{$output},"\t\t".'</math>');
			push(@{$output},"\t\t".'<listOfParameters>');
			push(@{$output},"\t\t\t".'<parameter id="LOWER_BOUND" value="'.$lb.'" units="mmol_per_gDW_per_hr"/>');
			push(@{$output},"\t\t\t".'<parameter id="UPPER_BOUND" value="'.$ub.'" units="mmol_per_gDW_per_hr"/>');
			push(@{$output},"\t\t\t".'<parameter id="OBJECTIVE_COEFFICIENT" value="0"/>');
			push(@{$output},"\t\t\t".'<parameter id="FLUX_VALUE" value="0.000000" units="mmol_per_gDW_per_hr"/>');
			push(@{$output},"\t\t".'</listOfParameters>');
			push(@{$output},"\t".'</kineticLaw>');
			push(@{$output},'</reaction>');
		}	
	}
	#Closing out the file
	push(@{$output},'</listOfReactions>');
	push(@{$output},'</model>');
	push(@{$output},'</sbml>');
	$output = join("\n",@{$output});
};

$logger->info("fbaModelServices export_fbamodel() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices export_fbamodel() warning messages\n".$stderr) if $stderr;
$logger->info("Export of FBAModel to SBML complete");

open(OUT, "> ".$opt->{workspace_name}."-".$opt->{object_name}."-SBML.xml");
print OUT $output;
close(OUT);

sub CleanNames {
	my ($name,$value) = @_;
	$value =~ s/[\s:,-]/_/g;
	$value =~ s/\W//g;
	return $name.'="'.$value.'"';
}