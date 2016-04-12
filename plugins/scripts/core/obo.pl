#! /usr/bin/env perl

use strict;
use Data::Dumper;
use JSON;
use Getopt::Long;

my $usage = <<"End_of_Usage";
Usage: $0 --to-json   ontology.obo  > ontology.json
       $0 --from-json ontology.json > ontology.obo

End_of_Usage

my ($help, $to_json, $from_json, $print_spec);

GetOptions("h|help"      => \$help,
           "t|to-json"   => \$to_json,
           "f|from-json" => \$from_json,
           "s|spec"      => \$print_spec
	  ) or die("Error in command line arguments\n");

if ($print_spec) {
    print_spec(); exit;
}

$help and die $usage;

my $input = shift @ARGV or die $usage;
my $ftype = guess_file_type($input);

if ($to_json || $ftype eq 'obo' && !$from_json) {
    obo_to_json($input);
} elsif ($from_json || $ftype eq 'json' && !$to_json) {
    json_to_obo($input);
} else {
    die "Unrecognized input file.\n";
}

sub obo_to_json {
    my ($input) = @_;
    open(OBO, "<$input") or die "Could not open $input";
    my $obj;
    my ($stanza, $type) = parse_stanza(\*OBO, 'Header');
    $obj->{header} = $stanza;
    while ($type) {
        my ($stanza, $section, $next_type);
        ($stanza, $next_type) = parse_stanza(\*OBO, $type);
        $section = lc($type)."_hash";
        $obj->{$section}->{$stanza->{id}} = $stanza;
        $type = $next_type;
    }
    close(OBO);
    print to_json($obj);
}

sub json_to_obo {
    my ($input) = @_;
    my $obj = from_json(slurp($input));
    write_stanza($obj->{header}, 'Header');
    my @types = qw(Term Typedef Instance);
    for my $type (@types) {
        my $key = lc($type)."_hash";
        next unless $obj->{$key};
        my @ids = sort keys %{$obj->{$key}};
        for my $id (@ids) {
            print "\n[$type]\n";
            write_stanza($obj->{$key}->{$id}, $type);
        }
    }
}

sub write_stanza {
    my ($hash, $type) = @_;
    my @tags = sort { tag_order($type, $a) <=> tag_order($type, $b) } keys %$hash;
    for my $k (@tags) {
        my $v = $hash->{$k};
        my $key = $type eq 'Header' ? json_key_to_header_tag($k) : $k;
        if (tag_multi($type, $k)) {
            print "$key: $_\n" for @$v;
        } else {
            print "$key: $v\n";
        }
    }
}

sub parse_stanza {
    my ($fh, $type) = @_;
    my $obj;
    while (<$fh>) {
        return ($obj, $1) if /^\[(\w+)\]/;
        my ($k, $v) = read_tag($_);
        $k && $v or next;
        $k =~ s/-/_/g;     # Header section uses -, and other sections use _
        if (tag_multi($type, $k)) {
            push @{$obj->{$k}}, $v;
        } else {
            $obj->{$k} = $v;
        }
    }
    return ($obj, undef);
}

sub read_tag {
    my ($line) = @_;
    my ($tag, $str) = $line =~ /(^\S*?):\s*(.*\S)/;
    $tag && $str or return;

    return ($tag, $str);
}

my $tag_info;
sub tag_order {
    my ($type, $tag) = @_;
    $tag_info ||= get_tag_info();
    # print STDERR '$tag_info = '. Dumper($tag_info);

    return $tag_info->{$type}->{$tag}->[0];
}
sub tag_multi {
    my ($type, $tag) = @_;
    $tag_info ||= get_tag_info();
    return $tag_info->{$type}->{$tag}->[1];
}
sub header_tag_to_json_key {
    my ($tag) = @_;
    $tag =~ s/-/_/g;
    return $tag;
}
sub json_key_to_header_tag {
    my ($tag) = @_;
    $tag =~ s/_/-/g;
    $tag =~ s/is-a/is_a/g;
    return $tag;
}


# https://oboformat.googlecode.com/svn/trunk/doc/GO.format.obo-1_2.html#S.2
sub get_tag_info {
    my @header_tag_order = qw(
                                 format-version
                                 data-version
                                 date
                                 saved-by
                                 auto-generated-by
                                 import
                                 subsetdef
                                 synonymtypedef
                                 default-namespace
                                 namespace-id-rule
                                 idspace
                                 treat-xrefs-as-equivalent
                                 treat-xrefs-as-genus-differentia
                                 treat-xrefs-as-relationship
                                 treat-xrefs-as-is_a
                                 remark
                                 ontology
                            );
    my @header_tag_multi = qw(
                                 import
                                 subsetdef
                                 synonymtypedef
                                 default-namespace
                                 namespace-id-rule
                                 idspace
                                 treat-xrefs-as-equivalent
                                 treat-xrefs-as-genus-differentia
                                 treat-xrefs-as-relationship
                                 treat-xrefs-as-is_a
                                 remark
                            );

    my @term_tag_order = qw(
                               id
                               is_anonymous
                               name
                               namespace
                               alt_id
                               def
                               comment
                               subset
                               synonym
                               xref
                               builtin
                               property_value
                               is_a
                               intersection_of
                               union_of
                               equivalent_to
                               disjoint_from
                               relationship
                               created_by
                               creation_date
                               is_obsolete
                               replaced_by
                               consider
                          );
    my @term_tag_multi = qw(
                               alt_id
                               def
                               comment
                               subset
                               synonym
                               xref
                               builtin
                               property_value
                               is_a
                               intersection_of
                               union_of
                               equivalent_to
                               disjoint_from
                               relationship
                               replaced_by
                               consider
                          );

    my @typedef_tag_order = qw(
                                  id
                                  is_anonymous
                                  name
                                  namespace
                                  alt_id
                                  def
                                  comment
                                  subset
                                  synonym
                                  xref
                                  property_value
                                  domain
                                  range
                                  builtin
                                  holds_over_chain
                                  is_anti_symmetric
                                  is_cyclic
                                  is_reflexive
                                  is_symmetric
                                  is_transitive
                                  is_functional
                                  is_inverse_functional
                                  is_a
                                  intersection_of
                                  union_of
                                  equivalent_to
                                  disjoint_from
                                  inverse_of
                                  transitive_over
                                  equivalent_to_chain
                                  disjoint_over
                                  relationship
                                  is_obsolete
                                  created_by
                                  creation_date
                                  replaced_by
                                  consider
                                  expand_assertion_to
                                  expand_expression_to
                                  is_metadata_tag
                                  is_class_level
                             );
    my @typedef_tag_multi = qw(
                                  alt_id
                                  def
                                  comment
                                  subset
                                  synonym
                                  xref
                                  property_value
                                  domain
                                  range
                                  builtin
                                  holds_over_chain
                                  is_a
                                  intersection_of
                                  union_of
                                  equivalent_to
                                  disjoint_from
                                  inverse_of
                                  transitive_over
                                  equivalent_to_chain
                                  disjoint_over
                                  relationship
                                  replaced_by
                                  consider
                                  expand_assertion_to
                                  expand_expression_to
                             );

    my @instance_tag_order = qw(
                                   id
                                   is_anonymous
                                   name
                                   namespace
                                   alt_id
                                   def
                                   comment
                                   subset
                                   synonym
                                   xref
                                   instance_of
                                   property_value
                                   relationship
                                   created_by
                                   creation_date
                                   is_obsolete
                                   replaced_by
                                   consider
                              );
    my @instance_tag_multi = qw(
                                   alt_id
                                   def
                                   comment
                                   subset
                                   synonym
                                   xref
                                   instance_of
                                   property_value
                                   relationship
                                   replaced_by
                                   consider
                              );

    my $header_tags   = make_tag_info_hash(\@header_tag_order, \@header_tag_multi);
    my $term_tags     = make_tag_info_hash(\@term_tag_order, \@term_tag_multi);
    my $typedef_tags  = make_tag_info_hash(\@typedef_tag_order, \@typedef_tag_multi);
    my $instance_tags = make_tag_info_hash(\@instance_tag_order, \@instance_tag_multi);

    return { Header   => $header_tags,
             Term     => $term_tags,
             Typedef  => $typedef_tags,
             Instance => $instance_tags
           };
}

sub make_tag_info_hash {
    my ($order_list, $multi_list) = @_;
    my (%hash, $i);
    $hash{$_} = [++$i] for map { s/-/_/g; $_ } @$order_list;
    $hash{$_}->[1] = 1 for map { s/-/_/g; $_ } @$multi_list;
    return \%hash;
}

sub print_spec {
    $tag_info ||= get_tag_info();
    print "module Ontology {\n\n";
    my @types = qw(Header Term Typedef Instance);
    for my $type (@types) {
        my @record;
        my @tags = sort { tag_order($type, $a) <=> tag_order($type, $b) } keys %{$tag_info->{$type}};
        for my $tag (@tags) {
            my $multi = tag_multi($type, $tag);
            my $var = $tag;
            my $def = $multi ? 'list<string>' : 'string';
            push @record, [$def, $var];
        }
        print_record('Ontology'.$type, \@record, 4);
    }
    my @record;
    push @record, [ 'OntologyHeader', 'header' ];
    shift @types;
    for my $type (@types) {
        push @record, [ "mapping<string, Ontology$type>", lc($type).'_hash' ];
    }
    print_record('OntologyDictionary', \@record, 4);
    print "};\n";
}

sub print_record {
    my ($struct, $record, $indent) = @_;
    my @lines;
    push @lines, 'typedef structure {';
    push @lines, '    '. $_->[0].' '. $_->[1].';' for @$record;
    push @lines, "} $struct;";
    print join('', ' 'x$indent, $_, "\n") for @lines;
    print "\n";
}

sub guess_file_type {
    my ($fname) = @_;
    my $head = '';
    open(F, "<$fname") or die "Could not open $fname";
    read(F, $head, 5000);
    close(F);
    if ($fname =~ /\.obo$/ || $head =~ /\[Term\]/) {
        return 'obo';
    } elsif ($fname =~ /\.json$/ || $head =~ /\s*{/) {
        return 'json';
    }
}

=head2 slurp

A fast file reader:

     $data = slurp( )               #  \*STDIN
     $data = slurp( \*FILEHANDLE )  #  an open file handle
     $data = slurp(  $filename )    #  a file name
     $data = slurp( "<$filename" )  #  file with explicit direction

=head3 Note

It is faster to read lines by reading the file and splitting
than by reading the lines sequentially.  If space is not an
issue, this is the way to go.  If space is an issue, then lines
or records should be processed one-by-one (rather than loading
the whole input into a string or array).

=cut

sub slurp {
    my ( $fh, $close );
    if ( $_[0] && ref $_[0] eq 'GLOB' ) {
        $fh = shift;
    } elsif ( $_[0] && ! ref $_[0] ) {
        my $file = shift;
        if ( -f $file                       ) {
        } elsif (    $file =~ /^<(.*)$/ && -f $1 ) {
            $file = $1;
        }                       # Explicit read
        else {
            return undef;
        }
        open( $fh, '<', $file ) or return undef;
        $close = 1;
    } else {
        $fh = \*STDIN;
        $close = 0;
    }
    my $out = '';
    my $inc = 1048576;
    my $end =       0;
    my $read;
    while ( $read = read( $fh, $out, $inc, $end ) ) {
        $end += $read;
    }
    close( $fh ) if $close;
    $out;
}
