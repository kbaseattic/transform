#! /usr/bin/env perl

use strict;
use Getopt::Long;
use Data::Dumper;
use JSON;

use Bio::KBase::HandleService;

my $usage = <<"End_of_Usage";

Usage: $0 [ options ]

Upload one or two FASTA/FASTQ files to the shock server.

Options:

  -h, --help                          - print this help message and exit
  -s, --shock_service_url  URL        - shock service URL (D = https://kbase.us/services/shock-api)
  -n, --handle_service_url URL        - handle service URL (D = https://kbase.us/services/handle_service)
  -o, --output_file_name   json       - output JSON file of KBaseAssembly.PairedEndLibrary type
  --token                  string     - token string
  -t, --type               string     - output KBaseAssembly type (PairedEndLibrary, SingleEndLibrary, ReferenceAssembly)

Options for PairedEndLibrary:

  -f, --input_file_name    path       - one or two read files (FASTA, FASTQ, or compressed forms)
  --insert                 float      - insert size mean
  --stdev                  float      - insert size standard deviation
  --outward                           - this flag is set if reads in the pair point outward

Options for SingleEndLibrary:

  -f, --input_file_name    path       - one read file (FASTA, FASTQ, or compressed forms)

Options for ReferenceAssembly:

  -f, --input_file_name    path       - one FASTA file containing a reference set of contigs
  --refname    text                   - genome name of the reference contig set

Examples:

  $0 -t PairedEndLibrary -d stage/path -f read1.fq -f read2.fq -insert 300 -stdev 60 -o pe.reads.json
  $0 -t SingleEndLibrary -d stage/path -f read.fasta -o se.reads.json
  $0 -t ReferenceAssembly -d stage/path -f genome.fa -o ref.json

End_of_Usage

my ($help, $shock_url, $handle_url);
my ($type, $token);
my (@inputs, $output);
my ($insert, $stdev, $outward, $refname);

my $rc = GetOptions("h|help"                 => \$help,
                    "s|shock_service_url=s"  => \$shock_url,
                    "n|handle_service_url=s" => \$handle_url,
                    "o|output_file_name=s"   => \$output,
                    "f|input_file_name=s"    => \@inputs,
                    "t|type=s"               => \$type,
                    "insert=f"               => \$insert,
                    "stdev=f"                => \$stdev,
                    "outward"                => \$outward,
                    "refname=s"              => \$refname);

$token      ||= $ENV{KB_AUTH_TOKEN};
$shock_url  ||= 'https://kbase.us/services/shock-api';
$handle_url ||= 'https://kbase.us/services/handle_service';

$help and die $usage;
$type && @inputs >= 1 && @inputs <= 2 or die $usage;

my $shock = { url => $shock_url, token => $token };
my $handle_service = Bio::KBase::HandleService->new($handle_url);

my $obj;

if ($type eq 'PairedEndLibrary') {
    $obj = upload_pe_lib($shock, \@inputs, $insert, $stdev, $outward);
} elsif ($type eq 'SingleEndLibrary') {
    $obj = upload_se_lib($shock, \@inputs);
} elsif ($type eq 'ReferenceAssembly') {
    $obj = upload_ref($shock, \@inputs, $refname);
} else {
    die "Unrecognized output type: $type\n";
}

print_output($output, encode_json($obj));

sub upload_pe_lib {
    my ($shock, $inputs, $insert, $stdev, $outward) = @_;

    my $obj;
    $obj->{interleaved} = 1 if @$inputs == 1;
    $obj->{insert_size_mean} = $insert if $insert;
    $obj->{insert_size_std_dev} = $stdev if $stdev;
    $obj->{read_orientation_outward} = 1 if $outward;

    my $i;
    for my $file (@$inputs) {
        $obj->{'handle_'.++$i} = validate_seq_file($file);
    }

    return upload_files_in_obj($obj, $shock);
}

sub upload_se_lib {
    my ($shock, $inputs) = @_;

    my $obj;
    my $file = $inputs->[0];
    $obj->{handle} = validate_seq_file($file);

    return upload_files_in_obj($obj, $shock);
}

sub upload_ref {
    my ($shock, $inputs, $refname) = @_;

    my $obj;
    my $file = $inputs->[0];
    $obj->{handle} = validate_seq_file($file);
    $obj->{reference_name} = $refname if $refname;

    return upload_files_in_obj($obj, $shock);
}

sub validate_seq_file {
    my ($file) = @_;
    -s $file or die "Invalid file: $file\n";
    my $name = $file;
    $name =~ s/\.(gz|gzip|bzip|bzip2|bz|bz2|zip)$//;
    $name =~ s/\.tar$//;
    $name =~ /\.(fasta|fastq|fa|fq|fna|bas\.h5|bax\.h5)$/ or die "Unrecognized file type: $file\n";
    $file =~ s|.*/||;
    return { file_name => $file, type => '_handle_to_be_' };
}

sub upload_files_in_obj {
    my ($obj, $shock) = @_;
    while (my ($k, $v) = each %$obj) {
        $obj->{$k} = update_handle($v, $shock) if is_handle($k, $v);
    }
    return $obj;
}

sub is_handle {
    my ($k, $v) = @_;
    return 1 if $k =~ /handle/ && $v && ref $v eq 'HASH' && $v->{file_name};
}

sub update_handle {
    my ($handle, $shock) = @_;

    my $file = $handle->{file_name};
    my $id = curl_post_file($file, $shock);

    $handle->{type} = 'shock';
    $handle->{url}  = $shock->{url};
    $handle->{id}   = $id;

    if ($handle_service) {
        my $hid = $handle_service->persist_handle($handle);
        $handle->{hid} = $hid;
    }

    return $handle;
}

sub curl_post_file {
    my ($file, $shock) = @_;
    my $token = $shock->{token};
    my $url   = $shock->{url};
    my $attr  = q('{"filetype":"reads"}'); # should reference have a different type?
    my $cmd   = 'curl --connect-timeout 10 -s -X POST -F attributes=@- -F upload=@'.$file." $url/node ";
    $cmd     .= " -H 'Authorization: OAuth $token'";
    my $out   = `echo $attr | $cmd` or die "Connection timeout uploading file to Shock: $file\n";
    my $json  = decode_json($out);
    $json->{status} == 200 or die "Error uploading file: $file\n".$json->{status}." ".$json->{error}->[0]."\n";
    return $json->{data}->{id};
}

sub print_output {
    my ($fname, $text) = @_;
    open(F, ">$fname") or die "Could not open $fname";
    print F $text;
    close(F);
}
