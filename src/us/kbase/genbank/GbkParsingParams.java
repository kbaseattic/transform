package us.kbase.genbank;

public class GbkParsingParams {
	private final boolean ignoreWrongFeatureLocation;
	
	public GbkParsingParams(boolean ignoreWrongFeatureLocation) {
		this.ignoreWrongFeatureLocation = ignoreWrongFeatureLocation;
	}
	
	public boolean isIgnoreWrongFeatureLocation() {
		return ignoreWrongFeatureLocation;
	}
}
