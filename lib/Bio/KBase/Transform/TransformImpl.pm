package Bio::KBase::Transform::TransformImpl;
use strict;
use Bio::KBase::Exceptions;
# Use Semantic Versioning (2.0.0-rc.1)
# http://semver.org 
our $VERSION = "0.1.0";

=head1 NAME

Transform

=head1 DESCRIPTION

Transform APIs

=cut

#BEGIN_HEADER
use Bio::KBase::Workflow::KBW;
#END_HEADER

sub new
{
    my($class, @args) = @_;
    my $self = {
    };
    bless $self, $class;
    #BEGIN_CONSTRUCTOR
    my %params;
    my @list = qw(ws_url ws_un ws_id ws_type erdb_url ws_pw);
    if ((my $e = $ENV{KB_DEPLOYMENT_CONFIG}) && -e $ENV{KB_DEPLOYMENT_CONFIG}) {  
      my $service = $ENV{KB_SERVICE_NAME};
      if (defined($service)) {
        my %Config = ();
        tie %Config, "Config::Simple", "$e";
        for my $p (@list) {
          my $v = $Config{"$service.$p"};
          if ($v) {
            $params{$p} = $v;
          }
        }
      }
    }
 
    # set default values for testing
    $params{ujs_url} = 'http://localhost:7083' if! defined $params{ujs_url};
    $params{ws_url} = 'http://localhost:7058' if! defined $params{ws_url};
    $params{shock_url} = 'http://localhost:7078' if! defined $params{shock_url};
    $params{awe_url} = 'http://localhost:7080' if! defined $params{awe_url};
    $params{clientgroups} = 'prod' if ! defined $params{clientgroups};
    $params{svc_ws_un} = 'kbasetest' if! defined $params{ws_un};
    #$params{svc_ws_pw} = '' if! defined $params{svc_ws_pw};
    $params{svc_ws_name} = 'loader_test' if! defined $params{ws_id};
    #END_CONSTRUCTOR

    if ($self->can('_init_instance'))
    {
	$self->_init_instance();
    }
    return $self;
}

=head1 METHODS



=head2 import_data

  $result = $obj->import_data($ImportParam)

=over 4

=item Parameter and return types

=begin html

<pre>
$ImportParam is an ImportParam
$result is a string
ImportParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	url has a value which is a string
	ws_name has a value which is a string
	obj_name has a value which is a string
	ext_source_name has a value which is a string
type_string is a string

</pre>

=end html

=begin text

$ImportParam is an ImportParam
$result is a string
ImportParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	url has a value which is a string
	ws_name has a value which is a string
	obj_name has a value which is a string
	ext_source_name has a value which is a string
type_string is a string


=end text



=item Description



=back

=cut

sub import_data
{
    my $self = shift;
    my($ImportParam) = @_;

    my @_bad_arguments;
    (ref($ImportParam) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument \"ImportParam\" (value was \"$ImportParam\")");
    if (@_bad_arguments) {
	my $msg = "Invalid arguments passed to import_data:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'import_data');
    }

    my $ctx = $Bio::KBase::Transform::Service::CallContext;
    my($result);
    #BEGIN import_data
    $result = Bio::KBase::Workflow::KBW::run_async($self, $ctx, $args);
    #END import_data
    my @_bad_returns;
    (!ref($result)) or push(@_bad_returns, "Invalid type for return variable \"result\" (value was \"$result\")");
    if (@_bad_returns) {
	my $msg = "Invalid returns passed to import_data:\n" . join("", map { "\t$_\n" } @_bad_returns);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'import_data');
    }
    return($result);
}




=head2 validate

  $result = $obj->validate($ValidateParam)

=over 4

=item Parameter and return types

=begin html

<pre>
$ValidateParam is a ValidateParam
$result is a reference to a list where each element is a string
ValidateParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	id has a value which is a shock_ref
type_string is a string
shock_ref is a reference to a hash where the following keys are defined:
	id has a value which is a shock_id
	shock_url has a value which is a string
shock_id is a string

</pre>

=end html

=begin text

$ValidateParam is a ValidateParam
$result is a reference to a list where each element is a string
ValidateParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	id has a value which is a shock_ref
type_string is a string
shock_ref is a reference to a hash where the following keys are defined:
	id has a value which is a shock_id
	shock_url has a value which is a string
shock_id is a string


=end text



=item Description



=back

=cut

sub validate
{
    my $self = shift;
    my($ValidateParam) = @_;

    my @_bad_arguments;
    (ref($ValidateParam) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument \"ValidateParam\" (value was \"$ValidateParam\")");
    if (@_bad_arguments) {
	my $msg = "Invalid arguments passed to validate:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'validate');
    }

    my $ctx = $Bio::KBase::Transform::Service::CallContext;
    my($result);
    #BEGIN validate
    $result = Bio::KBase::Workflow::KBW::run_async($self, $ctx, $args);
    #END validate
    my @_bad_returns;
    (ref($result) eq 'ARRAY') or push(@_bad_returns, "Invalid type for return variable \"result\" (value was \"$result\")");
    if (@_bad_returns) {
	my $msg = "Invalid returns passed to validate:\n" . join("", map { "\t$_\n" } @_bad_returns);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'validate');
    }
    return($result);
}




=head2 uploader

  $result = $obj->uploader($UploadParam)

=over 4

=item Parameter and return types

=begin html

<pre>
$UploadParam is an UploadParam
$result is a reference to a list where each element is a string
UploadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	in_id has a value which is a shock_ref
	ws_name has a value which is a string
	obj_name has a value which is a string
type_string is a string
shock_ref is a reference to a hash where the following keys are defined:
	id has a value which is a shock_id
	shock_url has a value which is a string
shock_id is a string

</pre>

=end html

=begin text

$UploadParam is an UploadParam
$result is a reference to a list where each element is a string
UploadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	in_id has a value which is a shock_ref
	ws_name has a value which is a string
	obj_name has a value which is a string
type_string is a string
shock_ref is a reference to a hash where the following keys are defined:
	id has a value which is a shock_id
	shock_url has a value which is a string
shock_id is a string


=end text



=item Description



=back

=cut

sub uploader
{
    my $self = shift;
    my($UploadParam) = @_;

    my @_bad_arguments;
    (ref($UploadParam) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument \"UploadParam\" (value was \"$UploadParam\")");
    if (@_bad_arguments) {
	my $msg = "Invalid arguments passed to uploader:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'uploader');
    }

    my $ctx = $Bio::KBase::Transform::Service::CallContext;
    my($result);
    #BEGIN uploader
    $result = Bio::KBase::Workflow::KBW::run_async($self, $ctx, $args);
    #END uploader
    my @_bad_returns;
    (ref($result) eq 'ARRAY') or push(@_bad_returns, "Invalid type for return variable \"result\" (value was \"$result\")");
    if (@_bad_returns) {
	my $msg = "Invalid returns passed to uploader:\n" . join("", map { "\t$_\n" } @_bad_returns);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'uploader');
    }
    return($result);
}




=head2 download

  $result = $obj->download($DownloadParam)

=over 4

=item Parameter and return types

=begin html

<pre>
$DownloadParam is a DownloadParam
$result is a reference to a list where each element is a string
DownloadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	out_id has a value which is a shock_ref
	ws_name has a value which is a string
	obj_name has a value which is a string
type_string is a string
shock_ref is a reference to a hash where the following keys are defined:
	id has a value which is a shock_id
	shock_url has a value which is a string
shock_id is a string

</pre>

=end html

=begin text

$DownloadParam is a DownloadParam
$result is a reference to a list where each element is a string
DownloadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	out_id has a value which is a shock_ref
	ws_name has a value which is a string
	obj_name has a value which is a string
type_string is a string
shock_ref is a reference to a hash where the following keys are defined:
	id has a value which is a shock_id
	shock_url has a value which is a string
shock_id is a string


=end text



=item Description



=back

=cut

sub download
{
    my $self = shift;
    my($DownloadParam) = @_;

    my @_bad_arguments;
    (ref($DownloadParam) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument \"DownloadParam\" (value was \"$DownloadParam\")");
    if (@_bad_arguments) {
	my $msg = "Invalid arguments passed to download:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'download');
    }

    my $ctx = $Bio::KBase::Transform::Service::CallContext;
    my($result);
    #BEGIN download
    #END download
    my @_bad_returns;
    (ref($result) eq 'ARRAY') or push(@_bad_returns, "Invalid type for return variable \"result\" (value was \"$result\")");
    if (@_bad_returns) {
	my $msg = "Invalid returns passed to download:\n" . join("", map { "\t$_\n" } @_bad_returns);
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
							       method_name => 'download');
    }
    return($result);
}




=head2 version 

  $return = $obj->version()

=over 4

=item Parameter and return types

=begin html

<pre>
$return is a string
</pre>

=end html

=begin text

$return is a string

=end text

=item Description

Return the module version. This is a Semantic Versioning number.

=back

=cut

sub version {
    return $VERSION;
}

=head1 TYPES



=head2 type_string

=over 4



=item Description

A type string copied from WS spec.
Specifies the type and its version in a single string in the format
[module].[typename]-[major].[minor]:

module - a string. The module name of the typespec containing the type.
typename - a string. The name of the type as assigned by the typedef
        statement. For external type, it start with “e_”.
major - an integer. The major version of the type. A change in the
        major version implies the type has changed in a non-backwards
        compatible way.
minor - an integer. The minor version of the type. A change in the
        minor version implies that the type has changed in a way that is
        backwards compatible with previous type definitions.

In many cases, the major and minor versions are optional, and if not
provided the most recent version will be used.

Example: MyModule.MyType-3.1


=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 shock_id

=over 4



=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 shock_ref

=over 4



=item Description

optional shock_url


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
id has a value which is a shock_id
shock_url has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
id has a value which is a shock_id
shock_url has a value which is a string


=end text

=back



=head2 Importer

=over 4



=item Description

mapping<string,string> optional_args; // optarg paramters


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
default_source_url has a value which is a string
script has a value which is a shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
default_source_url has a value which is a string
script has a value which is a shock_ref


=end text

=back



=head2 ImportParam

=over 4



=item Description

mapping<string, string> optional_args; // optarg key and values


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
url has a value which is a string
ws_name has a value which is a string
obj_name has a value which is a string
ext_source_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
url has a value which is a string
ws_name has a value which is a string
obj_name has a value which is a string
ext_source_name has a value which is a string


=end text

=back



=head2 Validator

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
validation_script has a value which is a shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
validation_script has a value which is a shock_ref


=end text

=back



=head2 ValidateParam

=over 4



=item Description

mapping<string, string> optional_args; // optarg key and values


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
id has a value which is a shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
id has a value which is a shock_ref


=end text

=back



=head2 Uploader

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
validator has a value which is a Validator
kb_type has a value which is a type_string
translation_script has a value which is a shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
validator has a value which is a Validator
kb_type has a value which is a type_string
translation_script has a value which is a shock_ref


=end text

=back



=head2 UploadParam

=over 4



=item Description

mapping<string, string> optional_args; // optarg key and values


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
in_id has a value which is a shock_ref
ws_name has a value which is a string
obj_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
in_id has a value which is a shock_ref
ws_name has a value which is a string
obj_name has a value which is a string


=end text

=back



=head2 Downloader

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
kb_type has a value which is a type_string
ext_type has a value which is a type_string
translation_script has a value which is a shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
kb_type has a value which is a type_string
ext_type has a value which is a type_string
translation_script has a value which is a shock_ref


=end text

=back



=head2 DownloadParam

=over 4



=item Description

mapping<string, string> optional_args; // optarg key and values


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
out_id has a value which is a shock_ref
ws_name has a value which is a string
obj_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
out_id has a value which is a shock_ref
ws_name has a value which is a string
obj_name has a value which is a string


=end text

=back



=cut

1;
