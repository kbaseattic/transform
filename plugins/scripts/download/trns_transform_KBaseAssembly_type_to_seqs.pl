#! /usr/bin/env perl

use strict;
use Data::Dumper;
use JSON::XS;
use Getopt::Long::Descriptive;
use Bio::KBase::workspace::Client;
use Bio::KBase::GenomeAnnotation::Client;
use Bio::KBase::Transform::ScriptHelpers qw(get_input_fh get_output_fh load_input write_output write_text_output genome_to_gto);

my($opt, $usage) = describe_options("%c %o",
				    ['workspace_service_url=s', 'Workspace URL', { default => 'https://kbase.us/services/ws/' }],
				    ['workspace_name=s', 'Workspace name', { required => 1 }],
				    ['object_name=s', 'Object name', { required => 1 }],
				    ['working_directory=s', 'Output directory for generated files', { required => 1 }],
				    ['object_version', 'Workspace object version'],
                                    ['token', 'KBase token', { default => $ENV{KB_AUTH_TOKEN}}],
				    ['help|h', 'show this help message'],
				   );

print($usage->text), exit  if $opt->help;
print($usage->text), exit 1 unless @ARGV == 0;

-d $opt->working_directory or die "Specified working directory " . $opt->working_directory . " does not exist\n";

my $wsclient = Bio::KBase::workspace::Client->new($opt->workspace_service_url);
my $ret = $wsclient->get_objects([{ workspace => $opt->workspace_name,
                                    name => $opt->object_name,
                                    (defined($opt->object_version) ? (ver => $opt->object_version) : ()) }]);

ref($ret) eq 'ARRAY' && @$ret && $ret->[0]->{data}
    or die sprintf("Workspace did not return an object for %s in %s at %s\n", $opt->object_name, $opt->workspace_name, $opt->workspace_service_url);

my $obj = $ret->[0];
my $type = type_of_object($obj);
my $data = $obj->{data};

my %supported = map { $_ => 1 }
                qw(KBaseAssembly.PairedEndLibrary
                   KBaseAssembly.SingleEndLibrary
                   KBaseAssembly.ReferenceAssembly
                   KBaseAssembly.AssemblyInput
                   KBaseFile.PairedEndLibrary
                   KBaseFile.SingleEndLibrary);

$supported{$type} or die "Unsupported object type: $type\n";

download_handles_in_data($data);

sub download_handles_in_data {
    my ($p) = @_;
    download_handle($p) if is_handle($p);
    if (ref($p) eq 'HASH') {
        download_handles_in_data($_) for values %$p;
    } elsif (ref($p) eq 'ARRAY') {
        download_handles_in_data($_) for @$p;
    }
}

sub download_handle {
    my ($handle) = @_;
    my $token = $opt->token;
    my $filename = get_handle_filename($handle, $token);
    my $outfile = $opt->working_directory .'/'. $filename;
    my $url = $handle->{url} . "/node/" . $handle->{id};
    my @auth_header;
    @auth_header = ("-H", "Authorization: OAuth $token") if $token;
    my @cmd = ("curl", "-s", @auth_header, '-o', $outfile, '-X', 'GET', "$url/?download");
    my $rc = system(@cmd);
    die "Failed to run: @cmd\n$!" if $rc != 0;
}

sub is_handle {
    my ($p) = @_;
    return 0 if ref($p) ne 'HASH';
    return 1 if $p->{type} eq 'shock' && $p->{id} && $p->{url};
}

sub type_of_object {
    my ($obj) = @_;
    my $fulltype = $obj->{info}->[2];
    my ($type) = $fulltype;
    $type =~ s/-[0-9.]*$//;
    return $type;
}

sub get_handle_filename {
    my ($handle, $token) = @_;

    my $url = $handle->{url} . "/node/" . $handle->{id};
    my $auth_header;
    $auth_header = "-H 'Authorization: OAuth $token'" if $token;
    my $cmd = "curl -s $auth_header -X GET $url";

    my $json = `$cmd 2> /dev/null`;
    die "Failed to run: $cmd\n$!" if $? == -1;

    my $ref = decode_json($json);
    return $ref->{data}->{file}->{name};
}
