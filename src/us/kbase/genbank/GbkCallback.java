package us.kbase.genbank;

import java.util.List;

/**
 * Results of parsing will be pushed back through implementation of this class.
 * @author rsutormin
 */
public interface GbkCallback {
	public void addHeaderTrackFile(String contigName, String headerType, String value, List<GbkSubheader> items, String filename) throws Exception;
    public void addFeatureTrackFile(String contigName, String featureType, int strand, int start, int stop, List<GbkLocation> locations, List<GbkQualifier> props, String filename) throws Exception;
    public void setGenomeTrackFile(String contigName, String genomeName, int taxId, String plasmid, String filename) throws Exception;
    public void addSeqPartTrackFile(String contigName, int seqPartIndex, String seqPart, int commonLen, String filename) throws Exception;
}
