use Bio::KBase::Transform::TransformImpl;

use Bio::KBase::Transform::Service;
use Plack::Middleware::CrossOrigin;



my @dispatch;

{
    my $obj = Bio::KBase::Transform::TransformImpl->new;
    push(@dispatch, 'Transform' => $obj);
}


my $server = Bio::KBase::Transform::Service->new(instance_dispatch => { @dispatch },
				allow_get => 0,
			       );

my $handler = sub { $server->handle_input(@_) };

$handler = Plack::Middleware::CrossOrigin->wrap( $handler, origins => "*", headers => "*");
