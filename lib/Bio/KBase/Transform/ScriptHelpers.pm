use strict;
use warnings;
package Bio::KBase::Transform::ScriptHelpers;
use Data::Dumper;
use Config::Simple;
use Getopt::Long::Descriptive;
use Text::Table;
use Bio::KBase::Auth;
use Exporter;
use File::Stream;
use parent qw(Exporter);
our @EXPORT_OK = qw( parse_input_table genome_to_gto contigs_to_gto );
use Bio::KBase::workspace::ScriptHelpers qw( get_ws_client workspace workspaceURL parseObjectMeta parseWorkspaceMeta printObjectMeta);

sub parse_input_table {
	my $filename = shift;
	my $columns = shift;#[name,required?(0/1),default,delimiter]
	if (!-e $filename) {
		print "Could not find input file:".$filename."!\n";
		exit();
	}
	if($filename !~ /\.([ct]sv|txt)$/){
    	die("$filename does not have correct suffix (.txt or .csv or .tsv)");
	}
	open(my $fh, "<", $filename) || return;
	my $headingline = <$fh>;
	chomp($headingline);
	my $delim = undef;
	if ($headingline =~ m/\t/) {
		$delim = "\\t";
	} elsif ($headingline =~ m/,/) {
		$delim = ",";
	}
	if (!defined($delim)) {
		die("$filename either does not use commas or tabs as a separator!");
	}
	my $headings = [split(/$delim/,$headingline)];
	my $data = [];
	while (my $line = <$fh>) {
		chomp($line);
		push(@{$data},[split(/$delim/,$line)]);
	}
	close($fh);
	my $headingColums;
	for (my $i=0;$i < @{$headings}; $i++) {
		$headingColums->{$headings->[$i]} = $i;
	}
	my $error = 0;
	for (my $j=0;$j < @{$columns}; $j++) {
		if (!defined($headingColums->{$columns->[$j]->[0]}) && defined($columns->[$j]->[1]) && $columns->[$j]->[1] == 1) {
			$error = 1;
			print "Model file missing required column '".$columns->[$j]->[0]."'!\n";
		}
	}
	if ($error == 1) {
		exit();
	}
	my $objects = [];
	foreach my $item (@{$data}) {
		my $object = [];
		for (my $j=0;$j < @{$columns}; $j++) {
			$object->[$j] = undef;
			if (defined($columns->[$j]->[2])) {
				$object->[$j] = $columns->[$j]->[2];
			}
			if (defined($headingColums->{$columns->[$j]->[0]}) && defined($item->[$headingColums->{$columns->[$j]->[0]}])) {
				$object->[$j] = $item->[$headingColums->{$columns->[$j]->[0]}];
			}
			if (defined($columns->[$j]->[3])) {
				if (defined($object->[$j]) && length($object->[$j]) > 0) {
					my $d = $columns->[$j]->[3];
					$object->[$j] = [split(/$d/,$object->[$j])];
				} else {
					$object->[$j] = [];
				}
			}
		}
		push(@{$objects},$object);
	}
	return $objects;
}

sub contigs_to_gto {
	my $contigs = shift;
	my $inputgenome = shift;
	if (!defined($inputgenome)) {
		$inputgenome = {
			genetic_code => 11,
			domain => "Bacteria",
			scientific_name => "Unknown sample"
		};
	}
	for (my $i=0; $i < @{$contigs->{contigs}}; $i++) {
		push(@{$inputgenome->{contigs}},{
			dna => $contigs->{contigs}->[$i]->{sequence},
			id => $contigs->{contigs}->[$i]->{id}
		});
	}
	return $inputgenome;
}

sub genome_to_gto {
	my $inputgenome = shift;	
	if (defined($inputgenome->{contigset_ref}) && $inputgenome->{contigset_ref} =~ m/^([^\/]+)\/([^\/]+)/) {
		my $ws = get_ws_client();
		my $contigws = $1;
		my $contigid = $2;
		my $input = {};
		if ($contigws =~ m/^\d+$/) {
			$input->{wsid} = $contigws;
		} else {
			$input->{workspace} = $contigws;
		}
		if ($contigid =~ m/^\d+$/) {
			$input->{objid} = $contigid;
		} else {
			$input->{name} = $contigid;
		}
		my $objdatas = $ws->get_objects([$input]);
		$inputgenome = contigs_to_gto($objdatas->[0]->{data},$inputgenome);
		delete $inputgenome->{contigset_ref};
	}
	return $inputgenome;
}

1;