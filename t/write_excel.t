use strict;
use Test::More;
use Data::Dumper;

BEGIN {
  use_ok( 'Spreadsheet::WriteExcel ' );
  use_ok( 'Bio::KBase::Transform::ScriptHelpers' );
}

use Bio::KBase::Transform::ScriptHelpers qw (write_excel_tables);
ok( my $wkbk = Spreadsheet::WriteExcel->new('filename'), "workbook is defined" );


my $long_name ="thisislongerthanthelimitof32charactersthatispermissibleforaworksheetname";
eval {my $sheet = $wkbk->add_worksheet($long_name); };
ok( $@, "bad table name caused exception: $@");


my $short_name = "thisisashortnname";
eval {my $sheet = $wkbk->add_worksheet($short_name); };
ok( $@ eq "", "good table name didn't cause exception: $@");



my $bad_char_name = 'thisisabadchar]';
eval {my $sheet = $wkbk->add_worksheet($bad_char_name); };
ok($@, "bad char in table name caused exception: $@");



done_testing;

