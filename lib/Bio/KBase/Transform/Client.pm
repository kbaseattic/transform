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


Transform Service

This KBase service supports translations and transformations of data types,
including converting external file formats to KBase objects, 
converting KBase objects to external file formats, and converting KBase objects
to other KBase objects, either objects of different types or objects of the same
type but different versions.


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
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
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

Returns the service version string.

=back

=cut

sub version
{
    my($self, @args) = @_;

# Authentication: none

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

  $results = $obj->methods($query)

=over 4

=item Parameter and return types

=begin html

<pre>
$query is a string
$results is a reference to a list where each element is a string

</pre>

=end html

=begin text

$query is a string
$results is a reference to a list where each element is a string


=end text

=item Description

Returns all available service methods, and info about them.

=back

=cut

sub methods
{
    my($self, @args) = @_;

# Authentication: none

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function methods (received $n, expecting 1)");
    }
    {
	my($query) = @args;

	my @_bad_arguments;
        (!ref($query)) or push(@_bad_arguments, "Invalid type for argument 1 \"query\" (value was \"$query\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to methods:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'methods');
	}
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



=head2 upload

  $result = $obj->upload($args)

=over 4

=item Parameter and return types

=begin html

<pre>
$args is an UploadParameters
$result is a reference to a list where each element is a string
UploadParameters is a reference to a hash where the following keys are defined:
	external_type has a value which is a string
	kbase_type has a value which is a type_string
	url_mapping has a value which is a reference to a hash where the key is a string and the value is a string
	workspace_name has a value which is a string
	object_name has a value which is a string
	object_id has a value which is a string
	options has a value which is a string
type_string is a string

</pre>

=end html

=begin text

$args is an UploadParameters
$result is a reference to a list where each element is a string
UploadParameters is a reference to a hash where the following keys are defined:
	external_type has a value which is a string
	kbase_type has a value which is a type_string
	url_mapping has a value which is a reference to a hash where the key is a string and the value is a string
	workspace_name has a value which is a string
	object_name has a value which is a string
	object_id has a value which is a string
	options has a value which is a string
type_string is a string


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
$args is a DownloadParameters
$result is a reference to a list where each element is a string
DownloadParameters is a reference to a hash where the following keys are defined:
	kbase_type has a value which is a type_string
	external_type has a value which is a string
	workspace_name has a value which is a string
	object_name has a value which is a string
	object_id has a value which is a string
	options has a value which is a string
type_string is a string

</pre>

=end html

=begin text

$args is a DownloadParameters
$result is a reference to a list where each element is a string
DownloadParameters is a reference to a hash where the following keys are defined:
	kbase_type has a value which is a type_string
	external_type has a value which is a string
	workspace_name has a value which is a string
	object_name has a value which is a string
	object_id has a value which is a string
	options has a value which is a string
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



=head2 convert

  $result = $obj->convert($args)

=over 4

=item Parameter and return types

=begin html

<pre>
$args is a ConvertParameters
$result is a reference to a list where each element is a string
ConvertParameters is a reference to a hash where the following keys are defined:
	source_kbase_type has a value which is a type_string
	source_workspace_name has a value which is a string
	source_object_name has a value which is a string
	source_object_id has a value which is a string
	destination_kbase_type has a value which is a type_string
	destination_workspace_name has a value which is a string
	destination_object_name has a value which is a string
	destination_object_id has a value which is a string
	options has a value which is a string
type_string is a string

</pre>

=end html

=begin text

$args is a ConvertParameters
$result is a reference to a list where each element is a string
ConvertParameters is a reference to a hash where the following keys are defined:
	source_kbase_type has a value which is a type_string
	source_workspace_name has a value which is a string
	source_object_name has a value which is a string
	source_object_id has a value which is a string
	destination_kbase_type has a value which is a type_string
	destination_workspace_name has a value which is a string
	destination_object_name has a value which is a string
	destination_object_id has a value which is a string
	options has a value which is a string
type_string is a string


=end text

=item Description



=back

=cut

sub convert
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function convert (received $n, expecting 1)");
    }
    {
	my($args) = @args;

	my @_bad_arguments;
        (ref($args) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"args\" (value was \"$args\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to convert:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'convert');
	}
    }

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
	method => "Transform.convert",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'convert',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method convert",
					    status_line => $self->{client}->status_line,
					    method_name => 'convert',
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
                method_name => 'convert',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method convert",
            status_line => $self->{client}->status_line,
            method_name => 'convert',
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



=head2 UploadParameters

=over 4



=item Description

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
external_type has a value which is a string
kbase_type has a value which is a type_string
url_mapping has a value which is a reference to a hash where the key is a string and the value is a string
workspace_name has a value which is a string
object_name has a value which is a string
object_id has a value which is a string
options has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
external_type has a value which is a string
kbase_type has a value which is a type_string
url_mapping has a value which is a reference to a hash where the key is a string and the value is a string
workspace_name has a value which is a string
object_name has a value which is a string
object_id has a value which is a string
options has a value which is a string


=end text

=back



=head2 DownloadParameters

=over 4



=item Description

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
kbase_type has a value which is a type_string
external_type has a value which is a string
workspace_name has a value which is a string
object_name has a value which is a string
object_id has a value which is a string
options has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
kbase_type has a value which is a type_string
external_type has a value which is a string
workspace_name has a value which is a string
object_name has a value which is a string
object_id has a value which is a string
options has a value which is a string


=end text

=back



=head2 ConvertParameters

=over 4



=item Description

json string


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
source_kbase_type has a value which is a type_string
source_workspace_name has a value which is a string
source_object_name has a value which is a string
source_object_id has a value which is a string
destination_kbase_type has a value which is a type_string
destination_workspace_name has a value which is a string
destination_object_name has a value which is a string
destination_object_id has a value which is a string
options has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
source_kbase_type has a value which is a type_string
source_workspace_name has a value which is a string
source_object_name has a value which is a string
source_object_id has a value which is a string
destination_kbase_type has a value which is a type_string
destination_workspace_name has a value which is a string
destination_object_name has a value which is a string
destination_object_id has a value which is a string
options has a value which is a string


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
