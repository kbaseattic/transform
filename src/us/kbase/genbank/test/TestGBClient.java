package us.kbase.genbank.test;

import us.kbase.common.service.JsonClientException;
import us.kbase.common.service.UnauthorizedException;
import us.kbase.kbasedataimport.ImportNcbiGenomeParams;
import us.kbase.kbasedataimport.KBaseDataImportClient;

import java.io.IOException;
import java.net.URL;

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 10/27/14
 * Time: 3:24 PM
 */
public class TestGBClient {

    final static String url = "https://140.221.66.224:7125";

    /**
     * @param args
     */
    public final static void main(String[] args) {

        String user = System.getProperty("test.user");
        String pwd = System.getProperty("test.pwd");
        try {
            KBaseDataImportClient kic = new KBaseDataImportClient(new URL(url),
                    user,
                    pwd);


            ImportNcbiGenomeParams input = new ImportNcbiGenomeParams();
            input.setGenomeName("NC_000907.1");
            input.setOutGenomeId("NC_000907.1");
            input.setOutGenomeWs("test_gb_upload");





            try {
                kic.importNcbiGenome(input);
            } catch (JsonClientException e) {
                e.printStackTrace();
            }

        } catch (UnauthorizedException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }


    }


}
