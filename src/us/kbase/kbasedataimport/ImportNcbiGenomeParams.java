
package us.kbase.kbasedataimport;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: import_ncbi_genome_params</p>
 * 
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "genome_name",
    "out_genome_ws",
    "out_genome_id"
})
public class ImportNcbiGenomeParams {

    @JsonProperty("genome_name")
    private String genomeName;
    @JsonProperty("out_genome_ws")
    private String outGenomeWs;
    @JsonProperty("out_genome_id")
    private String outGenomeId;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    @JsonProperty("genome_name")
    public String getGenomeName() {
        return genomeName;
    }

    @JsonProperty("genome_name")
    public void setGenomeName(String genomeName) {
        this.genomeName = genomeName;
    }

    public ImportNcbiGenomeParams withGenomeName(String genomeName) {
        this.genomeName = genomeName;
        return this;
    }

    @JsonProperty("out_genome_ws")
    public String getOutGenomeWs() {
        return outGenomeWs;
    }

    @JsonProperty("out_genome_ws")
    public void setOutGenomeWs(String outGenomeWs) {
        this.outGenomeWs = outGenomeWs;
    }

    public ImportNcbiGenomeParams withOutGenomeWs(String outGenomeWs) {
        this.outGenomeWs = outGenomeWs;
        return this;
    }

    @JsonProperty("out_genome_id")
    public String getOutGenomeId() {
        return outGenomeId;
    }

    @JsonProperty("out_genome_id")
    public void setOutGenomeId(String outGenomeId) {
        this.outGenomeId = outGenomeId;
    }

    public ImportNcbiGenomeParams withOutGenomeId(String outGenomeId) {
        this.outGenomeId = outGenomeId;
        return this;
    }

    @JsonAnyGetter
    public Map<String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public String toString() {
        return ((((((((("ImportNcbiGenomeParams"+" [genomeName=")+ genomeName)+", outGenomeWs=")+ outGenomeWs)+", outGenomeId=")+ outGenomeId)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
