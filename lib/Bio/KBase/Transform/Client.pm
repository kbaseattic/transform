package Bio::KBase::Transform::Client;

use JSON::RPC::Client;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
use Bio::KBase::AuthToken;

# Client version should match Impl version
# This is a Semantic Version number,
# http://semver.org
our $VERSION = "0.1.0";

=head1 NAME

Bio::KBase::Transform::Client

=head1 DESCRIPTION


Transform APIs


=cut

sub new
{
    my($class, $url, @args) = @_;
    

    my $self = {
	client => Bio::KBase::Transform::Client::RpcClient->new,
	url => $url,
    };

    #
    # This module requires authentication.
    #
    # We create an auth token, passing through the arguments that we were (hopefully) given.

    {
	my $token = Bio::KBase::AuthToken->new(@args);
	
	if (!$token->error_message)
	{
	    $self->{token} = $token->token;
	    $self->{client}->{token} = $token->token;
	}
        else
        {
	    #
	    # All methods in this module require authentication. In this case, if we
	    # don't have a token, we can't continue.
	    #
	    die "Authentication failed: " . $token->error_message;
	}
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
}




=head2 import_data

  $result = $obj->import_data($args)

=over 4

=item Parameter and return types

=begin html

<pre>
$args is a Transform.ImportParam
$result is a string
ImportParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
	url has a value which is a string
	ws_name has a value which is a string
	obj_name has a value which is a string
	ext_source_name has a value which is a string
type_string is a string

</pre>

=end html

=begin text

$args is a Transform.ImportParam
$result is a string
ImportParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
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
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function import_data (received $n, expecting 1)");
    }
    {
	my($args) = @args;

	my @_bad_arguments;
        (ref($args) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"args\" (value was \"$args\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to import_data:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'import_data');
	}
    }

    my $result = $self->{client}->call($self->{url}, {
	method => "Transform.import_data",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'import_data',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method import_data",
					    status_line => $self->{client}->status_line,
					    method_name => 'import_data',
				       );
    }
}



=head2 validate

  $result = $obj->validate($args)

=over 4

=item Parameter and return types

=begin html

<pre>
$args is a Transform.ValidateParam
$result is a reference to a list where each element is a string
ValidateParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
	in_id has a value which is a Transform.shock_id
	optional_args has a value which is a string
type_string is a string
shock_id is a string

</pre>

=end html

=begin text

$args is a Transform.ValidateParam
$result is a reference to a list where each element is a string
ValidateParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
	in_id has a value which is a Transform.shock_id
	optional_args has a value which is a string
type_string is a string
shock_id is a string


=end text

=item Description



=back

=cut

sub validate
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function validate (received $n, expecting 1)");
    }
    {
	my($args) = @args;

	my @_bad_arguments;
        (ref($args) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"args\" (value was \"$args\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to validate:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'validate');
	}
    }

    my $result = $self->{client}->call($self->{url}, {
	method => "Transform.validate",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'validate',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method validate",
					    status_line => $self->{client}->status_line,
					    method_name => 'validate',
				       );
    }
}



=head2 upload

  $result = $obj->upload($args)

=over 4

=item Parameter and return types

=begin html

<pre>
$args is a Transform.UploadParam
$result is a reference to a list where each element is a string
UploadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
	kb_type has a value which is a Transform.type_string
	in_id has a value which is a Transform.shock_id
	ws_name has a value which is a string
	obj_name has a value which is a string
	optional_args has a value which is a string
type_string is a string
shock_id is a string

</pre>

=end html

=begin text

$args is a Transform.UploadParam
$result is a reference to a list where each element is a string
UploadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
	kb_type has a value which is a Transform.type_string
	in_id has a value which is a Transform.shock_id
	ws_name has a value which is a string
	obj_name has a value which is a string
	optional_args has a value which is a string
type_string is a string
shock_id is a string


=end text

=item Description



=back

=cut

sub upload
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function upload (received $n, expecting 1)");
    }
    {
	my($args) = @args;

	my @_bad_arguments;
        (ref($args) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"args\" (value was \"$args\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to upload:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'upload');
	}
    }

    my $result = $self->{client}->call($self->{url}, {
	method => "Transform.upload",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'upload',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method upload",
					    status_line => $self->{client}->status_line,
					    method_name => 'upload',
				       );
    }
}



=head2 download

  $result = $obj->download($args)

=over 4

=item Parameter and return types

=begin html

<pre>
$args is a Transform.DownloadParam
$result is a reference to a list where each element is a string
DownloadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
	kb_type has a value which is a Transform.type_string
	out_id has a value which is a Transform.shock_id
	ws_name has a value which is a string
	obj_name has a value which is a string
type_string is a string
shock_id is a string

</pre>

=end html

=begin text

$args is a Transform.DownloadParam
$result is a reference to a list where each element is a string
DownloadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a Transform.type_string
	kb_type has a value which is a Transform.type_string
	out_id has a value which is a Transform.shock_id
	ws_name has a value which is a string
	obj_name has a value which is a string
type_string is a string
shock_id is a string


=end text

=item Description



=back

=cut

sub download
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function download (received $n, expecting 1)");
    }
    {
	my($args) = @args;

	my @_bad_arguments;
        (ref($args) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"args\" (value was \"$args\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to download:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'download');
	}
    }

    my $result = $self->{client}->call($self->{url}, {
	method => "Transform.download",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'download',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method download",
					    status_line => $self->{client}->status_line,
					    method_name => 'download',
				       );
    }
}



sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, {
        method => "Transform.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'download',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method download",
            status_line => $self->{client}->status_line,
            method_name => 'download',
        );
    }
}

sub _validate_version {
    my ($self) = @_;
    my $svr_version = $self->version();
    my $client_version = $VERSION;
    my ($cMajor, $cMinor) = split(/\./, $client_version);
    my ($sMajor, $sMinor) = split(/\./, $svr_version);
    if ($sMajor != $cMajor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Major version numbers differ.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor < $cMinor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Client minor version greater than Server minor version.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor > $cMinor) {
        warn "New client version available for Bio::KBase::Transform::Client\n";
    }
    if ($sMajor == 0) {
        warn "Bio::KBase::Transform::Client version is $svr_version. API subject to change.\n";
    }
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
id has a value which is a Transform.shock_id
shock_url has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
id has a value which is a Transform.shock_id
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
etype has a value which is a Transform.type_string
default_source_url has a value which is a string
script has a value which is a Transform.shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
default_source_url has a value which is a string
script has a value which is a Transform.shock_ref


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
etype has a value which is a Transform.type_string
url has a value which is a string
ws_name has a value which is a string
obj_name has a value which is a string
ext_source_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
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
etype has a value which is a Transform.type_string
validation_script has a value which is a Transform.shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
validation_script has a value which is a Transform.shock_ref


=end text

=back



=head2 ValidateParam

=over 4



=item Description

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
in_id has a value which is a Transform.shock_id
optional_args has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
in_id has a value which is a Transform.shock_id
optional_args has a value which is a string


=end text

=back



=head2 Uploader

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
validator has a value which is a Transform.Validator
kb_type has a value which is a Transform.type_string
translation_script has a value which is a Transform.shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
validator has a value which is a Transform.Validator
kb_type has a value which is a Transform.type_string
translation_script has a value which is a Transform.shock_ref


=end text

=back



=head2 UploadParam

=over 4



=item Description

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
kb_type has a value which is a Transform.type_string
in_id has a value which is a Transform.shock_id
ws_name has a value which is a string
obj_name has a value which is a string
optional_args has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
kb_type has a value which is a Transform.type_string
in_id has a value which is a Transform.shock_id
ws_name has a value which is a string
obj_name has a value which is a string
optional_args has a value which is a string


=end text

=back



=head2 Downloader

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
kb_type has a value which is a Transform.type_string
ext_type has a value which is a Transform.type_string
translation_script has a value which is a Transform.shock_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
kb_type has a value which is a Transform.type_string
ext_type has a value which is a Transform.type_string
translation_script has a value which is a Transform.shock_ref


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
etype has a value which is a Transform.type_string
kb_type has a value which is a Transform.type_string
out_id has a value which is a Transform.shock_id
ws_name has a value which is a string
obj_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a Transform.type_string
kb_type has a value which is a Transform.type_string
out_id has a value which is a Transform.shock_id
ws_name has a value which is a string
obj_name has a value which is a string


=end text

=back



=head2 Pair

=over 4



=item Description

Test script type


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
key has a value which is a string
value has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
key has a value which is a string
value has a value which is a string


=end text

=back



=head2 CommandConfig

=over 4



=item Description

optional argument that is provided by json string. key is argument name and the key is used for retrieving json string from upload,download api call and the value is the command line option such as '-k'


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
cmd_name has a value which is a string
cmd_args has a value which is a reference to a hash where the key is a string and the value is a string
cmd_description has a value which is a string
max_runtime has a value which is an int
opt_args has a value which is a reference to a hash where the key is a string and the value is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
cmd_name has a value which is a string
cmd_args has a value which is a reference to a hash where the key is a string and the value is a string
cmd_description has a value which is a string
max_runtime has a value which is an int
opt_args has a value which is a reference to a hash where the key is a string and the value is a string


=end text

=back



=head2 Type2CommandConfig

=over 4



=item Description

each external type validator or external type to internal type pair transformer script configuration


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
config_map has a value which is a reference to a hash where the key is a string and the value is a Transform.CommandConfig

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
config_map has a value which is a reference to a hash where the key is a string and the value is a Transform.CommandConfig


=end text

=back



=cut

package Bio::KBase::Transform::Client::RpcClient;
use base 'JSON::RPC::Client';

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $obj) = @_;
    my $result;

    if ($uri =~ /\?/) {
       $result = $self->_get($uri);
    }
    else {
        Carp::croak "not hashref." unless (ref $obj eq 'HASH');
        $result = $self->_post($uri, $obj);
    }

    my $service = $obj->{method} =~ /^system\./ if ( $obj );

    $self->status_line($result->status_line);

    if ($result->is_success) {

        return unless($result->content); # notification?

        if ($service) {
            return JSON::RPC::ServiceObject->new($result, $self->json);
        }

        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    elsif ($result->content_type eq 'application/json')
    {
        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    else {
        return;
    }
}


sub _post {
    my ($self, $uri, $obj) = @_;
    my $json = $self->json;

    $obj->{version} ||= $self->{version} || '1.1';

    if ($obj->{version} eq '1.0') {
        delete $obj->{version};
        if (exists $obj->{id}) {
            $self->id($obj->{id}) if ($obj->{id}); # if undef, it is notification.
        }
        else {
            $obj->{id} = $self->id || ($self->id('JSON::RPC::Client'));
        }
    }
    else {
        # $obj->{id} = $self->id if (defined $self->id);
	# Assign a random number to the id if one hasn't been set
	$obj->{id} = (defined $self->id) ? $self->id : substr(rand(),2);
    }

    my $content = $json->encode($obj);

    $self->ua->post(
        $uri,
        Content_Type   => $self->{content_type},
        Content        => $content,
        Accept         => 'application/json',
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
