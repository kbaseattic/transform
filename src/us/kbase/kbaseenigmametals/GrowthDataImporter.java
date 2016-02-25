package us.kbase.kbaseenigmametals;

import java.io.File;
import us.kbase.common.service.UObject;
import us.kbase.kbaseenigmametals.GrowthMatrixUploader;
import us.kbase.kbaseenigmametals.GrowthMatrix;

public class GrowthDataImporter {

	private String fileName = null;
	private String token = null;
	private Long workspaceId = null;

	
	public GrowthDataImporter (String fileName, Long workspaceId, String token) throws Exception{
		if (fileName == null) {
			System.out.println("cMonkey Expression data file name required");
		} else {
			this.fileName = fileName;
		}
		if (token == null) {
			throw new Exception("Token not assigned");
		} else {
			this.token = token;
		}
		
		if (workspaceId == null) {
			throw new Exception("Workspace name not assigned");
		} else {
			this.workspaceId = workspaceId;
		}

	}
	
	public void importMatrix (String matrixName) throws Exception {
		
		GrowthMatrixUploader uploader = new GrowthMatrixUploader();
		
		GrowthMatrix matrix = new GrowthMatrix();
		matrix.setName(matrixName);
		
		File inputFile = new File(this.fileName);
		
		matrix = uploader.generateGrowthMatrix(inputFile, matrix);
		//System.out.println(matrix.toString());
		WsDeluxeUtil.saveObjectToWorkspaceRef(UObject.transformObjectToObject(matrix, UObject.class), "KBaseEnigmaMetals.GrowthMatrix", workspaceId, matrixName, "https://ci.kbase.us/services/ws", token.toString());
	}
	

}
