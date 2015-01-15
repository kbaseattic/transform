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
use Digest::MD5;
use Spreadsheet::ParseExcel;
use Spreadsheet::ParseXLSX;
use parent qw(Exporter);
our @EXPORT_OK = qw( parse_input_table parse_excel genome_to_gto contigs_to_gto );
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

sub parse_excel {
    my $filename = shift;
    my $columns = shift;

    if(!$filename || !-f $filename){
	die("Cannot find $filename");
    }

    if($filename !~ /\.xlsx?$/){
	die("$filename does not have excel suffix (.xls or .xlsx)");
    }

    my $excel = '';
    if($filename =~ /\.xlsx$/){
	$excel = Spreadsheet::ParseXLSX->new();
    }else{
	$excel = Spreadsheet::ParseExcel->new();
    }	

    my $workbook = $excel->parse($filename);
    if(!defined $workbook){
	die("Unable to parse $filename\n");
    }

    $filename =~ s/\.xlsx?//;

    my @worksheets = $workbook->worksheets();
    my $sheets = {};
    foreach my $sheet (@worksheets){
	my $File="";
	my $Filename = $filename;
	foreach my $row ($sheet->{MinRow}..$sheet->{MaxRow}){
	    my $rowData = [];
	    foreach my $col ($sheet->{MinCol}..$sheet->{MaxCol}) {
		my $cell = $sheet->{Cells}[$row][$col];
		if(!$cell || !defined($cell->{Val})){
		    push(@{$rowData},"");
		}else{
		    push(@{$rowData},$cell->{Val});
		}
	    }
	    $File .= join("\t",@$rowData)."\n";
	}

	$Filename.="_".$sheet->{Name};
	$Filename.="_".join("",localtime()).".txt";

	open(OUT, "> $Filename");
	print OUT $File;
	close(OUT);

	$sheets->{$sheet->{Name}}=$Filename;
    }
    return $sheets;
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

sub gto_to_contigs {
	my $inputgenome = shift;
	my $contigs = {
		id => $inputgenome->{id},
		name => $inputgenome->{scientific_name},
		md5 => $inputgenome->{md5},
		source_id => $inputgenome->{source_id},
		source => $inputgenome->{source},
		type => "Organism",
		contigs => []
	};
	for (my $i=0; $i < @{$inputgenome->{contigs}}; $i++) {
		push(@{$contigs->{contigs}},{
			sequence => $inputgenome->{contigs}->[$i]->{dna},
			id => $inputgenome->{contigs}->[$i]->{id},
			"length" => length($inputgenome->{contigs}->[$i]->{dna}),
			name => $inputgenome->{contigs}->[$i]->{id},
			md5 => Digest::MD5::md5_hex($inputgenome->{contigs}->[$i]->{dna})
		});
	}
	return $contigs;
}

sub gto_to_genome {
	my $genome = shift;
	$genome->{gc_content} = 0.5;
	if (defined($genome->{gc})) {
		$genome->{gc_content} = $genome->{gc}+0;
		delete $genome->{gc};
	}
	$genome->{genetic_code} = $genome->{genetic_code}+0;
	if (!defined($genome->{source})) {
		$genome->{source} = "KBase";
		$genome->{source_id} = $genome->{id};
	}
	if ( defined($genome->{contigs}) && scalar(@{$genome->{contigs}})>0 ) {
		my $label = "dna";
		if (defined($genome->{contigs}->[0]->{seq})) {
			$label = "seq";
		}
		$genome->{num_contigs} = @{$genome->{contigs}};
		my $sortedcontigs = [sort { $a->{$label} cmp $b->{$label} } @{$genome->{contigs}}];
		my $str = "";
		for (my $i=0; $i < @{$sortedcontigs}; $i++) {
			if (length($str) > 0) {
				$str .= ";";
			}
			$str .= $sortedcontigs->[$i]->{$label};		
		}
		$genome->{dna_size} = length($str)+0;
		$genome->{md5} = Digest::MD5::md5_hex($str);
		#This is a problem here - we don't know WS, so we can't save contigset and must stick in genome
		$genome->{contigset} = gto_to_contigs($genome);
	}
	if (defined($genome->{features})) {
		for (my $i=0; $i < @{$genome->{features}}; $i++) {
			my $ftr = $genome->{features}->[$i];
			if (!defined($ftr->{type}) && $ftr->{id} =~ m/(\w+)\.\d+$/) {
				$ftr->{type} = $1;
			}
			if (defined($ftr->{protein_translation})) {
				$ftr->{protein_translation_length} = length($ftr->{protein_translation})+0;
				$ftr->{md5} = Digest::MD5::md5_hex($ftr->{protein_translation});
			}
			if (defined($ftr->{dna_sequence})) {
				$ftr->{dna_sequence_length} = length($ftr->{dna_sequence})+0;
			}
			if (defined($ftr->{quality}->{weighted_hit_count})) {
				$ftr->{quality}->{weighted_hit_count} = $ftr->{quality}->{weighted_hit_count}+0;
			}
			if (defined($ftr->{quality}->{hit_count})) {
				$ftr->{quality}->{hit_count} = $ftr->{quality}->{hit_count}+0;
			}
			if (defined($ftr->{annotations})) {
				delete $ftr->{annotations};
			}
			if (defined($ftr->{location})) {
				$ftr->{location}->[0]->[1] = $ftr->{location}->[0]->[1]+0;
				$ftr->{location}->[0]->[3] = $ftr->{location}->[0]->[3]+0;
			}
			delete $ftr->{feature_creation_event};
		}
	}
	delete $genome->{contigs};
	delete $genome->{feature_creation_event};
	delete $genome->{analysis_events};
	return $genome;
}

1;
