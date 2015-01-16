package Bio::KBase::Transform::Client;

use JSON::RPC::Client;
use POSIX;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
my $get_time = sub { time, 0 };
eval {
    require Time::HiRes;
    $get_time = sub { Time::HiRes::gettimeofday() };
};

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
	headers => [],
    };

    chomp($self->{hostname} = `hostname`);
    $self->{hostname} ||= 'unknown-host';

    #
    # Set up for propagating KBRPC_TAG and KBRPC_METADATA environment variables through
    # to invoked services. If these values are not set, we create a new tag
    # and a metadata field with basic information about the invoking script.
    #
    if ($ENV{KBRPC_TAG})
    {
	$self->{kbrpc_tag} = $ENV{KBRPC_TAG};
    }
    else
    {
	my ($t, $us) = &$get_time();
	$us = sprintf("%06d", $us);
	my $ts = strftime("%Y-%m-%dT%H:%M:%S.${us}Z", gmtime $t);
	$self->{kbrpc_tag} = "C:$0:$self->{hostname}:$$:$ts";
    }
    push(@{$self->{headers}}, 'Kbrpc-Tag', $self->{kbrpc_tag});

    if ($ENV{KBRPC_METADATA})
    {
	$self->{kbrpc_metadata} = $ENV{KBRPC_METADATA};
	push(@{$self->{headers}}, 'Kbrpc-Metadata', $self->{kbrpc_metadata});
    }

    if ($ENV{KBRPC_ERROR_DEST})
    {
	$self->{kbrpc_error_dest} = $ENV{KBRPC_ERROR_DEST};
	push(@{$self->{headers}}, 'Kbrpc-Errordest', $self->{kbrpc_error_dest});
    }

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
$args is an ImportParam
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

$args is an ImportParam
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

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
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
$args is a ValidateParam
$result is a reference to a list where each element is a string
ValidateParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	in_id has a value which is a shock_id
	optional_args has a value which is a string
type_string is a string
shock_id is a string

</pre>

=end html

=begin text

$args is a ValidateParam
$result is a reference to a list where each element is a string
ValidateParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	in_id has a value which is a shock_id
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

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
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
$args is an UploadParam
$result is a reference to a list where each element is a string
UploadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	in_id has a value which is a shock_id
	ws_name has a value which is a string
	obj_name has a value which is a string
	optional_args has a value which is a string
type_string is a string
shock_id is a string

</pre>

=end html

=begin text

$args is an UploadParam
$result is a reference to a list where each element is a string
UploadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	in_id has a value which is a shock_id
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

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
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
$args is a DownloadParam
$result is a reference to a list where each element is a string
DownloadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	ws_name has a value which is a string
	in_id has a value which is a string
	optional_args has a value which is a string
type_string is a string

</pre>

=end html

=begin text

$args is a DownloadParam
$result is a reference to a list where each element is a string
DownloadParam is a reference to a hash where the following keys are defined:
	etype has a value which is a type_string
	kb_type has a value which is a type_string
	ws_name has a value which is a string
	in_id has a value which is a string
	optional_args has a value which is a string
type_string is a string


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

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
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



=head2 version

  $result = $obj->version()

=over 4

=item Parameter and return types

=begin html

<pre>
$result is a string

</pre>

=end html

=begin text

$result is a string


=end text

=item Description

Returns the system version number
TODO: support specific function version

=back

=cut

sub version
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 0)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function version (received $n, expecting 0)");
    }

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
	method => "Transform.version",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'version',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method version",
					    status_line => $self->{client}->status_line,
					    method_name => 'version',
				       );
    }
}



=head2 methods

  $results = $obj->methods()

=over 4

=item Parameter and return types

=begin html

<pre>
$results is a reference to a list where each element is a string

</pre>

=end html

=begin text

$results is a reference to a list where each element is a string


=end text

=item Description

Returns all available functions

=back

=cut

sub methods
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 0)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function methods (received $n, expecting 0)");
    }

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
	method => "Transform.methods",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'methods',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method methods",
					    status_line => $self->{client}->status_line,
					    method_name => 'methods',
				       );
    }
}



=head2 method_types

  $results = $obj->method_types($func)

=over 4

=item Parameter and return types

=begin html

<pre>
$func is a string
$results is a reference to a list where each element is a string

</pre>

=end html

=begin text

$func is a string
$results is a reference to a list where each element is a string


=end text

=item Description

Returns supported types of the function.

=back

=cut

sub method_types
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function method_types (received $n, expecting 1)");
    }
    {
	my($func) = @args;

	my @_bad_arguments;
        (!ref($func)) or push(@_bad_arguments, "Invalid type for argument 1 \"func\" (value was \"$func\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to method_types:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'method_types');
	}
    }

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
	method => "Transform.method_types",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'method_types',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method method_types",
					    status_line => $self->{client}->status_line,
					    method_name => 'method_types',
				       );
    }
}



=head2 method_config

  $result = $obj->method_config($func, $type)

=over 4

=item Parameter and return types

=begin html

<pre>
$func is a string
$type is a string
$result is a CommandConfig
CommandConfig is a reference to a hash where the following keys are defined:
	cmd_name has a value which is a string
	cmd_args has a value which is a reference to a hash where the key is a string and the value is a string
	cmd_args_override has a value which is a reference to a hash where the key is a string and the value is a string
	cmd_description has a value which is a string
	max_runtime has a value which is an int
	opt_args has a value which is a reference to a hash where the key is a string and the value is a string

</pre>

=end html

=begin text

$func is a string
$type is a string
$result is a CommandConfig
CommandConfig is a reference to a hash where the following keys are defined:
	cmd_name has a value which is a string
	cmd_args has a value which is a reference to a hash where the key is a string and the value is a string
	cmd_args_override has a value which is a reference to a hash where the key is a string and the value is a string
	cmd_description has a value which is a string
	max_runtime has a value which is an int
	opt_args has a value which is a reference to a hash where the key is a string and the value is a string


=end text

=item Description

Returns CommandConfig for the function and type.
For validator, type has to be the form of <Associated KBase Module>.<external type>.
For instance, GenBank format (GBK) is associated to KBaseGenomes' typed object.
So, the external type should be KBaseGenomes.GBK, which can be find by method_types function call.
In case of transformer, it requires source type and KBase typed object.
<Associated KBase Module>.<external type>-to-<KBase Module>.<KBase type>. 
``KBaseGenomes.GBK-to-KBaseGenomes.Genome'' will be the input type for method_config

=back

=cut

sub method_config
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 2)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function method_config (received $n, expecting 2)");
    }
    {
	my($func, $type) = @args;

	my @_bad_arguments;
        (!ref($func)) or push(@_bad_arguments, "Invalid type for argument 1 \"func\" (value was \"$func\")");
        (!ref($type)) or push(@_bad_arguments, "Invalid type for argument 2 \"type\" (value was \"$type\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to method_config:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'method_config');
	}
    }

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
	method => "Transform.method_config",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'method_config',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method method_config",
					    status_line => $self->{client}->status_line,
					    method_name => 'method_config',
				       );
    }
}



sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
        method => "Transform.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'method_config',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method method_config",
            status_line => $self->{client}->status_line,
            method_name => 'method_config',
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

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
in_id has a value which is a shock_id
optional_args has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
in_id has a value which is a shock_id
optional_args has a value which is a string


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

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
in_id has a value which is a shock_id
ws_name has a value which is a string
obj_name has a value which is a string
optional_args has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
in_id has a value which is a shock_id
ws_name has a value which is a string
obj_name has a value which is a string
optional_args has a value which is a string


=end text

=back



=head2 DownloadParam

=over 4



=item Description

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
ws_name has a value which is a string
in_id has a value which is a string
optional_args has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
etype has a value which is a type_string
kb_type has a value which is a type_string
ws_name has a value which is a string
in_id has a value which is a string
optional_args has a value which is a string


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
cmd_args_override has a value which is a reference to a hash where the key is a string and the value is a string
cmd_description has a value which is a string
max_runtime has a value which is an int
opt_args has a value which is a reference to a hash where the key is a string and the value is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
cmd_name has a value which is a string
cmd_args has a value which is a reference to a hash where the key is a string and the value is a string
cmd_args_override has a value which is a reference to a hash where the key is a string and the value is a string
cmd_description has a value which is a string
max_runtime has a value which is an int
opt_args has a value which is a reference to a hash where the key is a string and the value is a string


=end text

=back



=head2 Type2CommandConfig

=over 4



=item Description

each external type validator or external type to internal type pair transformer script configuration 
"validator" => "KBaseGenome.GBK" => { "cmd_name" => "trns_validate_KBaseGenomes.GBK", ... } 
 where "validator" is the type of command and "transformer", "downloader", and "uploader" are supported;
 "KBaseGenomes.GBK" is the source type and KBaseGenomes is the module to use external GBK file type
 and for "transform" it requires the source type and the kb type togeter. 
 "transform" =>"KBaseGenomes.GBK-to-KBaseGenomes.Genome" => {"cmd_name" => "trns_transform_KBaseGenomes.GBK-to-KBaseGenomes.Genome", ... }


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
config_map has a value which is a reference to a hash where the key is a string and the value is a reference to a hash where the key is a string and the value is a CommandConfig

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
config_map has a value which is a reference to a hash where the key is a string and the value is a reference to a hash where the key is a string and the value is a CommandConfig


=end text

=back



=cut

package Bio::KBase::Transform::Client::RpcClient;
use base 'JSON::RPC::Client';
use POSIX;
use strict;

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $headers, $obj) = @_;
    my $result;


    {
	if ($uri =~ /\?/) {
	    $result = $self->_get($uri);
	}
	else {
	    Carp::croak "not hashref." unless (ref $obj eq 'HASH');
	    $result = $self->_post($uri, $headers, $obj);
	}

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
    my ($self, $uri, $headers, $obj) = @_;
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
	@$headers,
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
