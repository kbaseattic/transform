use Bio::KBase::Loader::LoaderImpl;

use Bio::KBase::Loader::Service;
use Plack::Middleware::CrossOrigin;



my @dispatch;

{
    my $obj = Bio::KBase::Loader::LoaderImpl->new;
    push(@dispatch, 'Loader' => $obj);
}


my $server = Bio::KBase::Loader::Service->new(instance_dispatch => { @dispatch },
				allow_get => 0,
			       );

my $handler = sub { $server->handle_input(@_) };

$handler = Plack::Middleware::CrossOrigin->wrap( $handler, origins => "*", headers => "*");
