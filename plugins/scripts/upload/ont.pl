#! /usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use JSON;
use Getopt::Long;

my $usage = <<"End_of_Usage";
Usage: $0 --from-obo ontology.obo  > ontology.json
       $0 --to-obo ontology.json > ontology.obo
       $0 --from-trans translation.txt > translation.json
       $0 --to-trans translation.json > translation.txt

End_of_Usage

my ($help, $print_spec, $from_obo, $to_obo, $from_trans, $to_trans, $first_dict, $second_dict);

GetOptions("h|help"      => \$help,
           "spec"        => \$print_spec,
           "from-obo"    => \$from_obo,
           "to-obo"      => \$to_obo,
           "from-trans"  => \$from_trans,
           "to-trans"    => \$to_trans,
	   "first-dict=s"  => \$first_dict,
	   "second-dict=s" => \$second_dict
	  ) or die("Error in command line arguments\n");

if ($print_spec) {
    print_spec(); exit;
}

$help and die $usage;

my $input = shift @ARGV or die $usage;
my $ftype = guess_file_type($input);

if ($from_obo && $ftype eq 'obo') {
    obo_to_json($input);
} elsif ($to_obo && $ftype eq 'json') {
    json_to_obo($input);
} elsif ($from_trans && $ftype eq 'trans') {
    trans_to_json($input,$first_dict,$second_dict);
} elsif ($to_trans && $ftype eq 'json') {
    json_to_trans($input);
} else {
    die "Unrecognized input file.\n";
}

sub obo_to_json {
    my ($input) = @_;
    open(OBO, "<$input") or die "Could not open $input";
    my ($stanza, $type) = parse_stanza(\*OBO, 'Header');
    my $obj = $stanza;
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
    write_stanza($obj, 'Header');
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

sub trans_to_json {
    my ($input,$ont1,$ont2) = @_;
    my @lines = split(/\n/, slurp($input));
    my @comment;
    my $trans;
    for (@lines) {
        if (/^\!\s*(.*?)/) {
            push @comment, $1;
            next;
        }
        next unless /\S+:\S+.* > .*\S+:\S+/;
        my ($term1, $name1, $name2, $term2) = /(^\S+:\S+)( \S.*?|) > (\S.*) ; (\S+:\S+$)/;
        if (!$ont1) {
            ($ont1) = $term1 =~ /(\S+):/;
            $ont1 = lc $ont1;
            $ont1 =~ s/-/_/g;
        }
        if (!$ont2) {
            ($ont2) = $term2 =~ /(\S+):/;
            $ont2 = lc $ont2;
            $ont2 =~ s/-/_/g;
        }
        $name1 =~ s/^\s*//;
        $trans->{$term1}->{name} = $name1 if $name1;
        my $equiv;
        $equiv->{equiv_term} = $term2;
        $equiv->{equiv_name} = $name2 if $name2;
        push @{$trans->{$term1}->{equiv_terms}}, $equiv;
    }
    my $obj;
    $obj->{comment} = join("\n", @comment) if @comment;
    $obj->{ontology1} = $ont1;
    $obj->{ontology2} = $ont2;
    $obj->{translation} = $trans;
    print to_json($obj);
}

sub json_to_trans {
    my ($input) = @_;
    my $obj = from_json(slurp($input));
    my $comment = $obj->{comment};
    if ($comment) {
        my @lines = split(/\n/, $comment);
        print map { "!$_\n" } @lines;
        print "!\n";
    }
    my $trans = $obj->{translation};
    my @terms = sort { cmp_ontology_terms($a, $b) } keys %$trans;
    for my $t (@terms) {
        for (@{$trans->{$t}->{equiv_terms}}) {
            print $t;
            print ' '.$trans->{$t}->{name} if $trans->{$t}->{name};
            print ' > ';
            print $_->{equiv_name}.' ; ' if $_->{equiv_name};
            print $_->{equiv_term}."\n";
        }
    }
}

sub cmp_ontology_terms {
    my ($t1, $t2) = @_;
    return $t1 cmp $t2;
}

sub write_stanza {
    my ($hash, $type) = @_;
    my @tags = sort { tag_order($type, $a) <=> tag_order($type, $b) }
               grep { tag_order($type, $_) } keys %$hash;
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
sub tag_required {
    my ($type, $tag) = @_;
    $tag_info ||= get_tag_info();
    return $tag_info->{$type}->{$tag}->[2];
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


# ftp://ftp.geneontology.org/pub/go/www/GO.format.obo-1_4.shtml
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
                                 namespace-id-rule
                                 idspace
                                 treat-xrefs-as-equivalent
                                 treat-xrefs-as-genus-differentia
                                 treat-xrefs-as-relationship
                                 treat-xrefs-as-is_a
                                 remark
                            );
    my @header_tag_required = qw(format-version);

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
    my @term_tag_required = qw(id);


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
    my @typedef_tag_required = qw(id);

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
    my @instance_tag_required = qw(id);

    my $header_tags   = make_tag_info_hash(\@header_tag_order,  \@header_tag_multi,    \@header_tag_required);
    my $term_tags     = make_tag_info_hash(\@term_tag_order,     \@term_tag_multi,     \@term_tag_required);
    my $typedef_tags  = make_tag_info_hash(\@typedef_tag_order,  \@typedef_tag_multi,  \@typedef_tag_required);
    my $instance_tags = make_tag_info_hash(\@instance_tag_order, \@instance_tag_multi, \@instance_tag_required);

    return { Header   => $header_tags,
             Term     => $term_tags,
             Typedef  => $typedef_tags,
             Instance => $instance_tags
           };
}

sub make_tag_info_hash {
    my ($order_list, $multi_list, $required_list) = @_;
    my (%hash, $i);
    $hash{$_} = [++$i] for map { s/-/_/g; $_ } @$order_list;
    $hash{$_}->[1] = 1 for map { s/-/_/g; $_ } @$multi_list;
    $hash{$_}->[2] = 1 for map { s/-/_/g; $_ } @$required_list;
    return \%hash;
}

sub print_spec {
    $tag_info ||= get_tag_info();
    print "module KBaseOntology {\n\n";
    my @types = qw(Term Typedef Instance);
    for my $type (@types) {
        my ($record, $optionals) = get_spec_record_for_type($type);
        print_record('Ontology'.$type, $record, 4, $optionals);
    }
    my ($base, $optionals) = get_spec_record_for_type('Header');
    push @$optionals, ('typedef_hash', 'instance_hash');
    for my $type (@types) {
        push @$base, [ "mapping<string, list<Ontology$type>>", lc($type).'_hash' ];
    }
    print_record('OntologyDictionary', $base, 4, $optionals);
    print get_ontology_translation_spec()."\n";
    print "};\n";
}

sub get_ontology_translation_spec {
    return <<'End_Translation';

    /*
       @optional equiv_name
    */
    typedef structure {
        string equiv_term;
        string equiv_name;
    } EquivalentTerm;

    /*
       @optional name
    */
    typedef structure {
        string name;
        list<EquivalentTerm> equiv_terms;
    } TranslationRecord;

    /*
       @optional comment
    */
    typedef structure {
        string comment;
        string ontology1;
        string ontology2;
        mapping<string, TranslationRecord> translation;
    } OntologyTranslation;
End_Translation
}

sub get_spec_record_for_type {
    my ($type) = @_;
    $tag_info ||= get_tag_info();
    my @record;
    my @tags = sort { tag_order($type, $a) <=> tag_order($type, $b) } keys %{$tag_info->{$type}};
    my @optionals = grep { ! tag_required($type, $_) } @tags;
    for my $tag (@tags) {
        my $multi = tag_multi($type, $tag);
        my $var = $tag;
        my $def = $multi ? 'list<string>' : 'string';
        push @record, [$def, $var];
    }
    return (\@record, \@optionals);
}

sub print_record {
    my ($struct, $record, $indent, $optionals) = @_;
    my @lines;
    print_record_optional_fields($optionals, $indent) if $optionals;
    push @lines, 'typedef structure {';
    push @lines, '    '. $_->[0].' '. $_->[1].';' for @$record;
    push @lines, "} $struct;";
    print join('', ' 'x$indent, $_, "\n") for @lines;
    print "\n";
}

sub print_record_optional_fields {
    my ($optionals, $indent) = @_;
    my $space = ' 'x$indent;
    print $space."/*\n";
    print $space.'    @optional '.join(' ', @$optionals);
    print "\n";
    print $space."*/\n";
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
    } elsif ($head =~ /\S+:\S+.* > .*\S+:\S+/ ) {
        return 'trans';
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
