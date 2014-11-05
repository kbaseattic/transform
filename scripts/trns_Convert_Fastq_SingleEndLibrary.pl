#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;

my ($ws,$name,$handle) = ($ARGV[0],$ARGV[1],$ARGV[2]);
($ws,$name,$handle) = ("seaver:PlantRecModels","Test_SEL","KBH_26");
exit if !$ws || !$name || !$handle;

use Bio::KBase::AuthToken;

my $Auth = Bio::KBase::AuthToken->new();

use Bio::KBase::HandleService;

my $HandleService_URL="http://140.221.67.78:7109";
my $HandleService = Bio::KBase::HandleService->new($HandleService_URL);
my $Handle = $HandleService->hids_to_handles([$handle])->[0];
print Dumper($Handle),"\n";

use SHOCK::Client;

#my $Shock_URL = "https://kbase.us/services/shock-api";
my $Shock_URL = "http://140.221.67.78:7078";
my $Shock_Client = SHOCK::Client->new($Shock_URL, $Auth->{token});
print $Handle->{id},"\n";
my $response = $Shock_Client->get("node/".$Handle->{id});
print Dumper($response),"\n";

#my $Name = $response->{data}{file}{name};
#$client->download_to_path($node,"/tmp/".$Name);

#@optional file_name remote_md5 remote_sha1
my %Handle_Hash = (hid => $handle, id => $node, url => $Shock_URL, type => "shock", file_name => "", remote_md5 => "", remote_sha1 => "");
if(exists($response->{data}{file}{name})){
    $Handle_Hash{file_name}=$response->{data}{file}{name};
}
if(exists($response->{data}{file}{checksum}{md5})){
    $Handle_Hash{remote_md5}=$response->{data}{file}{checksum}{md5};
}
if(exists($response->{data}{file}{checksum}{sha1})){
    $Handle_Hash{remote_sha1}=$response->{data}{file}{checksum}{sha1};
}

#@optional description
my %FileRef_Hash = ( file => \%Handle_Hash, encoding => "UTF8", type => "fastq", size => $response->{data}{file}{size}, description => "");

#@optional source source_id project_id
my %StrainSourceInfo_Hash = ( source => "", source_id => "", project_id => "" );

#@optional date description
my %Location_Hash = ( lat => 0.0, lon => 0.0, elevation => 0.0, date => "", description => "" );

#@optional genetic_code source ncbi_taxid organelle location
my %StrainInfo_Hash = ( genetic_code => 11, genus => "", species => "", strain => "", organelle => "", ncbi_axid => 3702, source => \%StrainSourceInfo_Hash, location => \%Location_Hash );

#@optional source source_id project_id
my %LibrarySourceInfo_Hash = ( source => "", source_id => "", project_id => "" );

#@optional gc_content source
my %SEL_Hash = ( lib => \%FileRef_Hash, strain => \%StrainInfo_Hash, source => \%LibrarySourceInfo_Hash, sequencing_tech => "", read_count => 0, read_size => 0, gc_content => 0.0 );

use Bio::KBase::workspace::Client;
my $WS_URL = "http://kbase.us/services/ws";
my $WSClient = Bio::KBase::workspace::Client->new($WS_URL);
$WSClient->{token}=$Auth->{token};
$WSClient->{client}->{token}=$Auth->{token};
#$WSClient->save_objects({workspace=>$ws,objects=>[{name=>$name,data=>\%SEL_Hash,type=>"KBaseFile.SingleEndLibrary"}]});

__END__

#use in reading in linebreaks '\r' & '\n'
use File::Stream;

#use in reading gzipped files
use IO::Uncompress::Gunzip qw(gunzip $GunzipError);

sub getFileHandle{
    my $file=shift;
    my $stream;
    
    my $fh = new IO::Uncompress::Gunzip($file,Transparent=>1) or die "IO::Uncompress::Gunzip failed on $file: $GunzipError\n";;
    $stream = (File::Stream->new($fh, separator => qr{[\cM\r\n]}))[1];
    return $stream;
}

my $filehandle = getFileHandle($file);
